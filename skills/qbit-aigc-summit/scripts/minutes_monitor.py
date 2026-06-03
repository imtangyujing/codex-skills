#!/usr/bin/env python3
"""Monitor Feishu minutes and fetch finished AIGC summit artifacts."""

from __future__ import annotations

import argparse
import dataclasses
import datetime as dt
import json
import pathlib
import re
import subprocess
import sys
import traceback
from typing import Any


DEFAULT_CHECK_HOURS = (12, 18)
DEFAULT_PAGE_SIZE = 30
DEFAULT_TIMEZONE = "Asia/Shanghai"
MODULE_NAME = "minutes_monitor"
FAILURE_STATUS = "失败"
VALID_STATE_STATUSES = {
    "待建稿",
    "已建总稿骨架",
    "待骨架确认",
    "已骨架确认",
    "已建单人空文档",
    "待妙记",
    "已发现妙记",
    "已拉取逐字稿",
    "已写入总稿",
    "待人工确认",
    "已人工确认",
    "已同步单人文档",
    "已导出Word",
    "已交付",
    FAILURE_STATUS,
}
READY_WORDS = ("done", "finish", "finished", "complete", "completed", "success", "ready")
WAITING_WORDS = (
    "processing",
    "transcribing",
    "uploading",
    "pending",
    "running",
    "converting",
    "generating",
)


@dataclasses.dataclass
class Target:
    id: str
    recording_no: str | None = None
    guest: str | None = None
    keywords: list[str] = dataclasses.field(default_factory=list)
    minute_token: str | None = None
    min_score: int = 30

    @classmethod
    def from_mapping(cls, raw: dict[str, Any]) -> "Target":
        recording_no = raw.get("recording_no") or raw.get("recording") or raw.get("no")
        guest = raw.get("guest") or raw.get("speaker") or raw.get("name")
        keywords = raw.get("keywords") or raw.get("keyword") or []
        if isinstance(keywords, str):
            keywords = [keywords]
        target_id = raw.get("id") or build_target_id(recording_no, guest, keywords)
        return cls(
            id=str(target_id),
            recording_no=str(recording_no) if recording_no not in (None, "") else None,
            guest=str(guest) if guest not in (None, "") else None,
            keywords=[str(item) for item in keywords if str(item).strip()],
            minute_token=raw.get("minute_token") or token_from_url(raw.get("minute_url") or raw.get("url")),
            min_score=int(raw.get("min_score") or 30),
        )

    def search_terms(self, global_keywords: list[str]) -> list[str]:
        terms: list[str] = []
        if self.recording_no:
            clean_no = normalize_recording_no(self.recording_no)
            if clean_no:
                terms.extend([f"录音{clean_no}", f"【录音{clean_no}】", clean_no])
        if self.guest:
            terms.append(self.guest)
        terms.extend(self.keywords)
        terms.extend(global_keywords)
        return unique([term.strip() for term in terms if term and term.strip()])


class MonitorError(RuntimeError):
    pass


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Search Feishu minutes by naming rules, fetch transcripts/artifacts, and update JSON status."
    )
    parser.add_argument("--targets", help="JSON file with a list or {'targets': [...]} target definitions")
    parser.add_argument("--status", default="minutes_monitor_status.json", help="JSON status file to update")
    parser.add_argument("--output-dir", default="minutes_artifacts", help="Directory passed to vc +notes")
    parser.add_argument("--start", help="Search start time, ISO8601 or YYYY-MM-DD")
    parser.add_argument("--end", help="Search end time, ISO8601 or YYYY-MM-DD")
    parser.add_argument("--keyword", action="append", default=[], help="Extra global search keyword")
    parser.add_argument("--recording-no", action="append", default=[], help="Single-run recording number")
    parser.add_argument("--guest", action="append", default=[], help="Single-run guest name")
    parser.add_argument("--minute-token", action="append", default=[], help="Known minute token")
    parser.add_argument("--owner-ids", default="me", help="Owner open_id list for minutes +search, comma-separated")
    parser.add_argument("--participant-ids", help="Participant open_id list for minutes +search, comma-separated")
    parser.add_argument(
        "--search-scope",
        choices=("owned", "participated", "involved", "all"),
        default="owned",
        help="Search owner, participant, both separately, or no owner/participant filter",
    )
    parser.add_argument("--page-size", type=int, default=DEFAULT_PAGE_SIZE, help="minutes +search page size, max 30")
    parser.add_argument("--max-pages", type=int, default=20, help="Safety cap per query")
    parser.add_argument("--min-score", type=int, default=30, help="Default match score threshold")
    parser.add_argument("--dry-run", action="store_true", help="Print planned commands and skip lark-cli execution")
    parser.add_argument("--force", action="store_true", help="Run outside 12:00/18:00 schedule windows")
    parser.add_argument("--check-hour", action="append", type=int, help="Allowed check hour, repeatable")
    parser.add_argument("--window-minutes", type=int, default=75, help="Allowed minutes after each check hour")
    parser.add_argument("--now", help="Override current time for tests, ISO8601")
    parser.add_argument("--timezone", default=DEFAULT_TIMEZONE, help="Timezone label recorded in status")
    parser.add_argument("--overwrite", action="store_true", help="Pass --overwrite to vc +notes")
    parser.add_argument("--lark-cli", default="lark-cli", help="Path to lark-cli")
    parser.add_argument("--as-identity", default="user", help="lark-cli identity, usually user")
    parser.add_argument("--json", action="store_true", help="Keep JSON stdout; retained for caller clarity")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    status_path = pathlib.Path(args.status)
    output: dict[str, Any] = {
        "ok": False,
        "dry_run": args.dry_run,
        "status_path": str(status_path),
        "planned_commands": [],
        "targets": [],
        "errors": [],
    }

    try:
        now = parse_now(args.now)
        check_hours = tuple(args.check_hour or DEFAULT_CHECK_HOURS)
        due = args.force or is_check_window(now, check_hours, args.window_minutes)
        output.update(
            {
                "checked_at": now.isoformat(),
                "timezone": args.timezone,
                "check_hours": list(check_hours),
                "check_due": due,
            }
        )

        status = load_status(status_path)
        start_run(status, output)
        targets = load_targets(args)
        if not targets:
            raise MonitorError("No targets supplied. Use --targets or --recording-no/--guest/--minute-token.")

        if not due:
            output["ok"] = True
            output["status"] = "skipped_outside_schedule"
            for target in targets:
                output["targets"].append({"id": target.id, "status": "skipped_outside_schedule"})
            finish_run(status, output)
            write_status_unless_dry_run(status_path, status, args.dry_run)
            print_json(output)
            return 0

        cli = LarkCLI(args, output["planned_commands"])
        seen_minutes: dict[str, dict[str, Any]] = {}

        for target in targets:
            target.min_score = target.min_score or args.min_score
            result = process_target(args, cli, target, seen_minutes)
            output["targets"].append(result)
            update_target_status(status, result)
            write_status_unless_dry_run(status_path, status, args.dry_run)

        output["ok"] = not any(item.get("status") == "error" for item in output["targets"])
        output["status"] = "completed" if output["ok"] else "completed_with_errors"
        finish_run(status, output)
        write_status_unless_dry_run(status_path, status, args.dry_run)
        print_json(output)
        return 0 if output["ok"] else 2
    except Exception as exc:
        output["status"] = "error"
        output["error"] = str(exc)
        output["errors"].append({"message": str(exc), "traceback": traceback.format_exc(limit=5)})
        try:
            status = load_status(status_path)
            append_state_event(
                status,
                item_id=MODULE_NAME,
                state_status=FAILURE_STATUS,
                message="minutes monitor failed before target updates completed",
                error=str(exc),
                retry_reason="检查目标清单、命令参数或飞书CLI权限后重试",
                data={"dry_run": args.dry_run},
            )
            write_status_unless_dry_run(status_path, status, args.dry_run)
        except Exception as status_exc:
            output["status_write_error"] = str(status_exc)
        print_json(output)
        return 1


def process_target(
    args: argparse.Namespace,
    cli: "LarkCLI",
    target: Target,
    seen_minutes: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    result: dict[str, Any] = {
        "id": target.id,
        "recording_no": target.recording_no,
        "guest": target.guest,
        "keywords": target.keywords,
        "status": "pending",
    }
    try:
        if target.minute_token:
            minute = {"token": target.minute_token, "source": "target.minute_token"}
        else:
            candidates = search_candidates(args, cli, target, seen_minutes)
            if args.dry_run:
                result["candidate_count"] = 0
                result["status"] = "dry_run_planned"
                result["message"] = "Search commands planned; no Feishu data fetched."
                return result
            ranked = rank_candidates(target, candidates)
            result["candidate_count"] = len(candidates)
            result["ranked"] = ranked[:5]
            if not ranked or ranked[0]["score"] < target.min_score:
                result["status"] = "not_found"
                result["message"] = "No candidate matched target naming rules."
                return result
            minute = ranked[0]["minute"]

        result["minute_token"] = minute_token(minute)
        result["minute_title"] = minute_title(minute)
        result["minute_url"] = minute_url(minute)
        if not result["minute_token"]:
            result["status"] = "error"
            result["message"] = "Matched minute has no token."
            return result

        readiness = readiness_status(minute)
        result["readiness"] = readiness
        if readiness == "waiting":
            result["status"] = "recording_processing"
            result["message"] = "Minute exists, artifact generation is still processing."
            return result

        notes = cli.notes(result["minute_token"])
        result["notes"] = summarize_notes(notes)
        result["status"] = "dry_run_planned" if args.dry_run else "fetched"
        return result
    except Exception as exc:
        result["status"] = "error"
        result["message"] = str(exc)
        return result


def search_candidates(
    args: argparse.Namespace,
    cli: "LarkCLI",
    target: Target,
    seen_minutes: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    terms = target.search_terms(args.keyword)
    if not terms and not (args.start or args.end):
        raise MonitorError(f"Target {target.id} has no search terms or time range.")

    local_minutes: dict[str, dict[str, Any]] = {}
    for term in terms or [""]:
        for scope in search_scopes(args):
            page_token: str | None = None
            for _page in range(max(1, args.max_pages)):
                payload = cli.search(query=term, scope=scope, page_token=page_token)
                for item in extract_items(payload):
                    key = minute_key(item)
                    if key:
                        seen_minutes[key] = item
                        local_minutes[key] = item
                page_token = next_page_token(payload)
                if not has_more(payload) or not page_token:
                    break

    return list(local_minutes.values())


def search_scopes(args: argparse.Namespace) -> list[dict[str, str]]:
    if args.search_scope == "owned":
        return [{"owner_ids": args.owner_ids}] if args.owner_ids else [{}]
    if args.search_scope == "participated":
        return [{"participant_ids": args.participant_ids or "me"}]
    if args.search_scope == "involved":
        scopes = []
        if args.owner_ids:
            scopes.append({"owner_ids": args.owner_ids})
        scopes.append({"participant_ids": args.participant_ids or "me"})
        return scopes
    return [{}]


class LarkCLI:
    def __init__(self, args: argparse.Namespace, planned_commands: list[list[str]]) -> None:
        self.args = args
        self.planned_commands = planned_commands

    def search(self, query: str, scope: dict[str, str], page_token: str | None) -> dict[str, Any]:
        argv = [
            self.args.lark_cli,
            "minutes",
            "+search",
            "--as",
            self.args.as_identity,
            "--format",
            "json",
            "--page-size",
            str(min(max(1, self.args.page_size), 30)),
        ]
        if query:
            argv += ["--query", query]
        if self.args.start:
            argv += ["--start", self.args.start]
        if self.args.end:
            argv += ["--end", self.args.end]
        if scope.get("owner_ids"):
            argv += ["--owner-ids", scope["owner_ids"]]
        if scope.get("participant_ids"):
            argv += ["--participant-ids", scope["participant_ids"]]
        if page_token:
            argv += ["--page-token", page_token]
        return self.run(argv)

    def notes(self, token: str) -> dict[str, Any]:
        argv = [
            self.args.lark_cli,
            "vc",
            "+notes",
            "--as",
            self.args.as_identity,
            "--format",
            "json",
            "--minute-tokens",
            token,
            "--output-dir",
            self.args.output_dir,
        ]
        if self.args.overwrite:
            argv.append("--overwrite")
        return self.run(argv)

    def run(self, argv: list[str]) -> dict[str, Any]:
        self.planned_commands.append(argv)
        if self.args.dry_run:
            return {"dry_run": True, "argv": argv, "items": []}
        proc = subprocess.run(argv, text=True, capture_output=True, check=False)
        if proc.returncode != 0:
            raise MonitorError(command_error(argv, proc))
        try:
            return json.loads(proc.stdout or "{}")
        except json.JSONDecodeError as exc:
            raise MonitorError(f"Invalid JSON from {' '.join(argv[:3])}: {exc}") from exc


def load_targets(args: argparse.Namespace) -> list[Target]:
    targets: list[Target] = []
    if args.targets:
        raw = json.loads(pathlib.Path(args.targets).read_text(encoding="utf-8"))
        raw_targets = raw.get("targets", raw) if isinstance(raw, dict) else raw
        if not isinstance(raw_targets, list):
            raise MonitorError("--targets must be a list or {'targets': [...]}.")
        targets.extend(Target.from_mapping(item) for item in raw_targets)

    max_len = max(len(args.recording_no), len(args.guest), len(args.minute_token), 0)
    for index in range(max_len):
        raw = {
            "recording_no": item_at(args.recording_no, index),
            "guest": item_at(args.guest, index),
            "minute_token": item_at(args.minute_token, index),
            "keywords": args.keyword,
            "min_score": args.min_score,
        }
        targets.append(Target.from_mapping(raw))
    return targets


def rank_candidates(target: Target, candidates: list[dict[str, Any]]) -> list[dict[str, Any]]:
    ranked = []
    for minute in candidates:
        score, reasons = score_minute(target, minute)
        ranked.append({"score": score, "reasons": reasons, "minute": compact_minute(minute)})
    return sorted(ranked, key=lambda item: item["score"], reverse=True)


def score_minute(target: Target, minute: dict[str, Any]) -> tuple[int, list[str]]:
    title = normalize_text(minute_title(minute))
    blob = normalize_text(json.dumps(minute, ensure_ascii=False))
    score = 0
    reasons: list[str] = []

    token = minute_token(minute)
    if target.minute_token and token == target.minute_token:
        return 100, ["minute_token"]

    if target.recording_no:
        no = normalize_recording_no(target.recording_no)
        variants = [normalize_text(f"录音{no}"), normalize_text(f"【录音{no}】")]
        if any(variant in title for variant in variants):
            score += 60
            reasons.append("recording_no_in_title")
        elif no and no in title:
            score += 20
            reasons.append("recording_no_fragment")

    if target.guest and normalize_text(target.guest) in title:
        score += 40
        reasons.append("guest_in_title")
    elif target.guest and normalize_text(target.guest) in blob:
        score += 15
        reasons.append("guest_in_metadata")

    for keyword in target.keywords:
        needle = normalize_text(keyword)
        if needle and needle in title:
            score += 12
            reasons.append(f"keyword_in_title:{keyword}")
        elif needle and needle in blob:
            score += 5
            reasons.append(f"keyword_in_metadata:{keyword}")

    return score, reasons


def readiness_status(minute: dict[str, Any]) -> str:
    raw_values = []
    for key in ("status", "recording_status", "process_status", "transcript_status", "artifact_status"):
        value = deep_get(minute, key)
        if value not in (None, ""):
            raw_values.append(str(value).lower())
    text = " ".join(raw_values)
    if not text:
        return "unknown_assume_ready"
    if any(word in text for word in WAITING_WORDS):
        return "waiting"
    if any(word in text for word in READY_WORDS):
        return "ready"
    return "unknown_assume_ready"


def summarize_notes(payload: dict[str, Any]) -> dict[str, Any]:
    if payload.get("dry_run"):
        return {"dry_run": True, "argv": payload.get("argv")}
    notes = payload.get("notes") or deep_get(payload, "data.notes") or []
    artifacts = payload.get("artifacts") or deep_get(payload, "data.artifacts") or {}
    summary: dict[str, Any] = {
        "note_count": len(notes) if isinstance(notes, list) else 0,
        "has_artifacts": bool(artifacts),
    }
    if isinstance(notes, list) and notes:
        summary["notes"] = [
            {
                "note_doc_token": item.get("note_doc_token"),
                "verbatim_doc_token": item.get("verbatim_doc_token"),
                "transcript_file": deep_get(item, "artifacts.transcript_file"),
            }
            for item in notes
            if isinstance(item, dict)
        ]
    if isinstance(artifacts, dict):
        summary["artifact_keys"] = sorted(artifacts.keys())
        if artifacts.get("transcript_file"):
            summary["transcript_file"] = artifacts.get("transcript_file")
    return summary


def extract_items(payload: dict[str, Any]) -> list[dict[str, Any]]:
    if payload.get("dry_run"):
        return []
    for path in ("items", "data.items", "minutes", "data.minutes"):
        value = deep_get(payload, path)
        if isinstance(value, list):
            return [item for item in value if isinstance(item, dict)]
    return []


def has_more(payload: dict[str, Any]) -> bool:
    value = deep_get(payload, "has_more")
    if value is None:
        value = deep_get(payload, "data.has_more")
    return bool(value)


def next_page_token(payload: dict[str, Any]) -> str | None:
    value = deep_get(payload, "page_token")
    if value is None:
        value = deep_get(payload, "data.page_token")
    return str(value) if value else None


def compact_minute(minute: dict[str, Any]) -> dict[str, Any]:
    return {
        "token": minute_token(minute),
        "title": minute_title(minute),
        "url": minute_url(minute),
        "create_time": minute.get("create_time") or minute.get("created_at"),
        "status": minute.get("status") or minute.get("recording_status") or minute.get("process_status"),
    }


def minute_key(minute: dict[str, Any]) -> str:
    return minute_token(minute) or minute_url(minute) or minute_title(minute)


def minute_token(minute: dict[str, Any]) -> str:
    for key in ("token", "minute_token", "id"):
        value = minute.get(key)
        if value:
            return str(value)
    return token_from_url(minute_url(minute)) or ""


def minute_title(minute: dict[str, Any]) -> str:
    for key in ("title", "name", "topic"):
        value = minute.get(key)
        if value:
            return str(value)
    return ""


def minute_url(minute: dict[str, Any]) -> str:
    for key in ("url", "minute_url", "share_url"):
        value = minute.get(key)
        if value:
            return str(value)
    return ""


def token_from_url(value: Any) -> str | None:
    if not value:
        return None
    text = str(value).split("?")[0].rstrip("/")
    match = re.search(r"/minutes/([^/]+)$", text)
    if match:
        return match.group(1)
    if re.fullmatch(r"[A-Za-z0-9_-]{8,}", text):
        return text
    return None


def normalize_recording_no(value: str | None) -> str:
    if not value:
        return ""
    match = re.search(r"\d+", str(value))
    return match.group(0) if match else str(value).strip()


def normalize_text(value: str | None) -> str:
    text = str(value or "").lower()
    return re.sub(r"[-\s\[\]【】（）()_:：#]+", "", text)


def unique(items: list[str]) -> list[str]:
    seen = set()
    result = []
    for item in items:
        if item not in seen:
            result.append(item)
            seen.add(item)
    return result


def build_target_id(recording_no: Any, guest: Any, keywords: list[str]) -> str:
    pieces = [str(item) for item in (recording_no, guest) if item not in (None, "")]
    if not pieces:
        pieces = keywords[:2] or ["target"]
    return "-".join(normalize_text(piece) or "target" for piece in pieces)


def item_at(items: list[str], index: int) -> str | None:
    return items[index] if index < len(items) else None


def deep_get(data: Any, path: str) -> Any:
    current = data
    for part in path.split("."):
        if isinstance(current, dict):
            current = current.get(part)
        else:
            return None
    return current


def parse_now(value: str | None) -> dt.datetime:
    if value:
        return dt.datetime.fromisoformat(value)
    return dt.datetime.now().astimezone()


def is_check_window(now: dt.datetime, hours: tuple[int, ...], window_minutes: int) -> bool:
    for hour in hours:
        start = now.replace(hour=hour, minute=0, second=0, microsecond=0)
        end = start + dt.timedelta(minutes=window_minutes)
        if start <= now <= end:
            return True
    return False


def load_status(path: pathlib.Path) -> dict[str, Any]:
    if not path.exists():
        return {"schema_version": 1, "items": {}, "events": []}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(data, dict):
            data.setdefault("schema_version", 1)
            data.setdefault("items", {})
            data.setdefault("events", [])
            return data
    except json.JSONDecodeError:
        pass
    return {"schema_version": 1, "items": {}, "events": [], "previous_status_unreadable": True}


def start_run(status: dict[str, Any], output: dict[str, Any]) -> None:
    status.setdefault("schema_version", 1)
    status.setdefault("items", {})
    status.setdefault("events", [])


def finish_run(status: dict[str, Any], output: dict[str, Any]) -> None:
    status.setdefault("schema_version", 1)
    status.setdefault("items", {})
    status.setdefault("events", [])


def update_target_status(status: dict[str, Any], result: dict[str, Any]) -> None:
    run_status = result.get("status")
    if run_status == "dry_run_planned":
        return

    state_status = state_status_for_result(result)
    if state_status is None:
        return

    append_state_event(
        status,
        item_id=str(result.get("id")),
        state_status=state_status,
        message=result.get("message") or default_state_message(run_status),
        error=result.get("message") if state_status == FAILURE_STATUS else None,
        retry_reason=retry_reason_for_result(result) if state_status == FAILURE_STATUS else None,
        data=state_data_for_result(result),
    )


def state_status_for_result(result: dict[str, Any]) -> str | None:
    run_status = result.get("status")
    if run_status == "fetched":
        return "已拉取逐字稿"
    if run_status == "recording_processing":
        return "已发现妙记"
    if run_status in {"not_found", "skipped_outside_schedule"}:
        return "待妙记"
    if run_status == "error":
        return FAILURE_STATUS
    return None


def default_state_message(run_status: Any) -> str:
    return {
        "fetched": "已拉取妙记逐字稿和AI产物",
        "recording_processing": "已发现妙记，等待产物生成",
        "not_found": "当前范围内未找到命名匹配的妙记",
        "skipped_outside_schedule": "当前时间不在检查窗口内",
        "error": "妙记监控失败",
    }.get(str(run_status), "妙记监控状态更新")


def retry_reason_for_result(result: dict[str, Any]) -> str:
    message = str(result.get("message") or "")
    if "permission" in message.lower() or "scope" in message.lower():
        return "补齐飞书CLI权限后重试"
    if "No targets" in message:
        return "补齐目标清单后重试"
    return "确认妙记标题、时间范围、token或网络状态后重试"


def state_data_for_result(result: dict[str, Any]) -> dict[str, Any]:
    keys = (
        "recording_no",
        "guest",
        "keywords",
        "minute_token",
        "minute_title",
        "minute_url",
        "readiness",
        "notes",
        "candidate_count",
    )
    return {key: result.get(key) for key in keys if result.get(key) not in (None, "", [])}


def append_state_event(
    status: dict[str, Any],
    *,
    item_id: str,
    state_status: str,
    message: str | None = None,
    error: str | None = None,
    retry_reason: str | None = None,
    data: dict[str, Any] | None = None,
) -> None:
    if state_status not in VALID_STATE_STATUSES:
        raise MonitorError(f"Invalid state status: {state_status}")
    if state_status == FAILURE_STATUS and (not error or not retry_reason):
        raise MonitorError("Failure state requires error and retry_reason.")

    now = dt.datetime.now().astimezone().isoformat(timespec="seconds")
    event: dict[str, Any] = {
        "at": now,
        "item_id": item_id,
        "module": MODULE_NAME,
        "status": state_status,
    }
    if message:
        event["message"] = message
    if error:
        event["error"] = error
    if retry_reason:
        event["retry_reason"] = retry_reason
    if data:
        event["data"] = data

    items = status.setdefault("items", {})
    item = items.setdefault(item_id, {"id": item_id, "history": []})
    item.update({"status": state_status, "updated_at": now, "updated_by": MODULE_NAME})
    if data:
        item.setdefault("data", {}).update(data)
    if error:
        item["error"] = error
    elif state_status != FAILURE_STATUS:
        item.pop("error", None)
    if retry_reason:
        item["retry_reason"] = retry_reason
    elif state_status != FAILURE_STATUS:
        item.pop("retry_reason", None)
    item.setdefault("history", []).append(event)
    status.setdefault("events", []).append(event)


def write_status_unless_dry_run(path: pathlib.Path, status: dict[str, Any], dry_run: bool) -> None:
    if dry_run:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(status, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def command_error(argv: list[str], proc: subprocess.CompletedProcess[str]) -> str:
    stderr = proc.stderr.strip()
    stdout = proc.stdout.strip()
    detail = stderr or stdout or "no output"
    return f"Command failed ({proc.returncode}): {' '.join(argv)}\n{detail}"


def print_json(payload: dict[str, Any]) -> None:
    print(json.dumps(payload, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    raise SystemExit(main())
