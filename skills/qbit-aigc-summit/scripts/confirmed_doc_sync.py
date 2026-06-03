#!/usr/bin/env python3
"""Sync confirmed summit sections into their target Lark documents."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import tempfile
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import state_store


SCRIPT_NAME = "confirmed_doc_sync"
CONFIRMED_STATUSES = {"confirmed", "approved", "ready_to_sync", "ready"}


class SyncError(Exception):
    """A recoverable sync failure with item context."""


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def read_payload(path: str | None) -> dict[str, Any]:
    if path:
        with open(path, "r", encoding="utf-8") as handle:
            return json.load(handle)
    raw = sys.stdin.read()
    if not raw.strip():
        raise SyncError("missing JSON input on stdin; pass --input or pipe JSON")
    return json.loads(raw)


def emit(payload: dict[str, Any], pretty: bool) -> None:
    kwargs = {"ensure_ascii": False}
    if pretty:
        kwargs["indent"] = 2
    print(json.dumps(payload, **kwargs))


def run_json(argv: list[str], dry_run: bool = False) -> dict[str, Any]:
    completed = subprocess.run(argv, text=True, capture_output=True, check=False)
    command_result = {
        "argv": argv,
        "returncode": completed.returncode,
        "stdout": completed.stdout,
        "stderr": completed.stderr,
    }
    if completed.returncode != 0:
        raise SyncError(
            f"command failed({completed.returncode}): {' '.join(argv)}\n{completed.stderr.strip()}"
        )
    if not completed.stdout.strip():
        return {"_command": command_result}
    try:
        parsed = json.loads(completed.stdout)
    except json.JSONDecodeError:
        parsed = {"raw_stdout": completed.stdout}
    if isinstance(parsed, dict):
        parsed.setdefault("_command", command_result if dry_run else {"argv": argv})
        return parsed
    return {"value": parsed, "_command": command_result if dry_run else {"argv": argv}}


def recursive_find(obj: Any, key: str) -> Any:
    if isinstance(obj, dict):
        if key in obj:
            return obj[key]
        for value in obj.values():
            found = recursive_find(value, key)
            if found is not None:
                return found
    elif isinstance(obj, list):
        for value in obj:
            found = recursive_find(value, key)
            if found is not None:
                return found
    return None


def extract_content(fetch_result: dict[str, Any]) -> str:
    for key in ("content", "xml", "markdown", "text"):
        value = recursive_find(fetch_result, key)
        if isinstance(value, str) and value.strip():
            return value
    raise SyncError("fetch result did not include document content")


def compact_error(exc: BaseException) -> str:
    text = str(exc).strip()
    return text if len(text) <= 2000 else text[:1997] + "..."


def ensure_parent(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def atomic_write_json(path: Path, payload: dict[str, Any]) -> None:
    ensure_parent(path)
    with tempfile.NamedTemporaryFile(
        "w", encoding="utf-8", dir=str(path.parent), delete=False
    ) as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2)
        handle.write("\n")
        temp_name = handle.name
    os.replace(temp_name, path)


def load_status(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    with open(path, "r", encoding="utf-8") as handle:
        loaded = json.load(handle)
    if not isinstance(loaded, dict):
        raise SyncError(f"status_path must contain a JSON object: {path}")
    return loaded


def write_status(
    path_text: str | None,
    run_id: str,
    items: list[dict[str, Any]],
    dry_run: bool,
) -> dict[str, Any] | None:
    if not path_text:
        return None
    status_path = Path(path_text).expanduser()
    updates: list[dict[str, Any]] = []
    for item in items:
        item_status = str(item.get("status") or "")
        if item_status == "synced":
            updates.append(
                state_store.update_status(
                    path=status_path,
                    item_id=str(item["id"]),
                    module=SCRIPT_NAME,
                    status="已同步单人文档",
                    message="已把总稿确认section同步到目标文档",
                    data=item,
                    dry_run=dry_run,
                )
            )
        elif item_status == "failed":
            updates.append(
                state_store.update_status(
                    path=status_path,
                    item_id=str(item["id"]),
                    module=SCRIPT_NAME,
                    status=state_store.FAILURE_STATUS,
                    error=str(item.get("error") or "sync failed"),
                    retry_reason="检查总稿section、目标文档、block id和Feishu权限后重试",
                    data=item,
                    dry_run=dry_run,
                )
            )
        elif item_status == "skipped":
            updates.append(
                state_store.update_status(
                    path=status_path,
                    item_id=str(item["id"]),
                    module=SCRIPT_NAME,
                    status="待人工确认",
                    message="该section尚未确认，暂不同步",
                    data=item,
                    dry_run=dry_run,
                )
            )

    return {
        "updated_at": utc_now(),
        "run_id": run_id,
        "dry_run": dry_run,
        "items": {str(item["id"]): item for item in items},
        "state_updates": updates,
    }


def is_confirmed(section: dict[str, Any]) -> bool:
    if section.get("confirmed") is True:
        return True
    status = str(
        section.get("status")
        or section.get("review_status")
        or section.get("confirmation_status")
        or ""
    ).strip().lower()
    return status in CONFIRMED_STATUSES


def section_id(section: dict[str, Any], index: int) -> str:
    return str(
        section.get("id")
        or section.get("section_id")
        or section.get("speaker")
        or section.get("title")
        or f"section_{index:02d}"
    )


def source_doc_for(payload: dict[str, Any], section: dict[str, Any]) -> str:
    source = section.get("source_doc") or section.get("master_doc") or payload.get("master_doc")
    if not source:
        raise SyncError("section is missing source_doc and payload.master_doc")
    return str(source)


def content_from_section(
    payload: dict[str, Any],
    section: dict[str, Any],
    as_identity: str | None,
    dry_run: bool,
) -> tuple[str | None, dict[str, Any] | None]:
    direct = (
        section.get("confirmed_content")
        or section.get("content")
        or section.get("xml")
        or section.get("markdown")
    )
    if isinstance(direct, str) and direct.strip():
        return direct, None

    start_block_id = (
        section.get("start_block_id")
        or section.get("source_block_id")
        or section.get("block_id")
    )
    if not start_block_id:
        if dry_run:
            return None, {
                "planned_fetch": "content omitted; provide content or source block id for real sync"
            }
        raise SyncError("confirmed section has no content or source block id")

    argv = [
        "lark-cli",
        "docs",
        "+fetch",
        "--api-version",
        "v2",
        "--doc",
        source_doc_for(payload, section),
        "--doc-format",
        str(section.get("source_format") or payload.get("doc_format") or "xml"),
        "--format",
        "json",
        "--detail",
        str(section.get("source_detail") or "full"),
        "--scope",
        str(section.get("source_scope") or "section"),
        "--start-block-id",
        str(start_block_id),
    ]
    end_block_id = section.get("end_block_id")
    if end_block_id:
        argv.extend(["--end-block-id", str(end_block_id)])
    if section.get("max_depth") is not None:
        argv.extend(["--max-depth", str(section["max_depth"])])
    if as_identity:
        argv.extend(["--as", as_identity])
    if dry_run:
        argv.append("--dry-run")
        return None, {"planned_fetch": argv}
    fetched = run_json(argv)
    return extract_content(fetched), {"fetch": {"argv": argv}}


def target_doc(section: dict[str, Any]) -> str:
    target = (
        section.get("target_doc")
        or section.get("target_url")
        or section.get("doc")
        or section.get("url")
    )
    if not target:
        raise SyncError("confirmed section is missing target_doc")
    return str(target)


def update_command(section: dict[str, Any]) -> str:
    command = str(section.get("command") or "").strip()
    if command:
        return command
    if section.get("target_block_id"):
        return "block_replace"
    if section.get("pattern"):
        return "str_replace"
    return "append"


def build_update_argv(
    section: dict[str, Any],
    content_path: str,
    as_identity: str | None,
    dry_run: bool,
) -> list[str]:
    command = update_command(section)
    argv = [
        "lark-cli",
        "docs",
        "+update",
        "--api-version",
        "v2",
        "--doc",
        target_doc(section),
        "--command",
        command,
        "--doc-format",
        str(section.get("target_format") or section.get("doc_format") or "xml"),
        "--content",
        f"@{content_path}",
    ]
    target_block_id = section.get("target_block_id")
    if target_block_id:
        argv.extend(["--block-id", str(target_block_id)])
    pattern = section.get("pattern")
    if pattern:
        argv.extend(["--pattern", str(pattern)])
    if section.get("revision_id") is not None:
        argv.extend(["--revision-id", str(section["revision_id"])])
    if as_identity:
        argv.extend(["--as", as_identity])
    if dry_run:
        argv.append("--dry-run")
    return argv


def sync_one(
    payload: dict[str, Any],
    section: dict[str, Any],
    index: int,
    as_identity: str | None,
    dry_run: bool,
) -> dict[str, Any]:
    item_id = section_id(section, index)
    base = {
        "id": item_id,
        "target_doc": section.get("target_doc") or section.get("target_url"),
        "target_kind": section.get("target_kind") or section.get("kind"),
        "updated_at": utc_now(),
    }
    if not is_confirmed(section):
        return {**base, "status": "skipped", "reason": "not_confirmed"}

    content, evidence = content_from_section(payload, section, as_identity, dry_run)
    if dry_run:
        planned_update = None
        try:
            planned_update = build_update_argv(
                section,
                "<confirmed-section-content>" if content else "<fetched-confirmed-section>",
                as_identity,
                dry_run=True,
            )
        except Exception as exc:  # noqa: BLE001 - dry-run should still return fetch evidence
            planned_update = {"error": compact_error(exc)}
        planned = deepcopy(base)
        planned.update(
            {
                "status": "planned",
                "command": update_command(section),
                "evidence": evidence,
                "planned_update": planned_update,
            }
        )
        if content:
            planned["content_bytes"] = len(content.encode("utf-8"))
        return planned

    if content is None:
        raise SyncError("no content available for real sync")

    with tempfile.NamedTemporaryFile("w", encoding="utf-8", suffix=".xml", delete=False) as handle:
        handle.write(content)
        content_path = handle.name
    try:
        argv = build_update_argv(section, content_path, as_identity, dry_run=False)
        update_result = run_json(argv)
        return {
            **base,
            "status": "synced",
            "command": update_command(section),
            "content_bytes": len(content.encode("utf-8")),
            "evidence": evidence,
            "update": update_result,
        }
    finally:
        try:
            os.unlink(content_path)
        except FileNotFoundError:
            pass


def normalize_sections(payload: dict[str, Any]) -> list[dict[str, Any]]:
    sections = payload.get("sections") or payload.get("items")
    if not isinstance(sections, list):
        raise SyncError("input must include sections or items as a list")
    return [section for section in sections if isinstance(section, dict)]


def run(payload: dict[str, Any], cli_dry_run: bool) -> dict[str, Any]:
    dry_run = bool(cli_dry_run or payload.get("dry_run"))
    run_id = str(payload.get("run_id") or f"{SCRIPT_NAME}_{utc_now()}")
    as_identity = payload.get("as") or payload.get("identity")
    sections = normalize_sections(payload)
    results: list[dict[str, Any]] = []
    ok = True

    for index, section in enumerate(sections, start=1):
        item_id = section_id(section, index)
        try:
            results.append(sync_one(payload, section, index, as_identity, dry_run))
        except Exception as exc:  # noqa: BLE001 - script must report item-level failures
            ok = False
            failure = {
                "id": item_id,
                "status": "failed",
                "target_doc": section.get("target_doc") or section.get("target_url"),
                "updated_at": utc_now(),
                "error": compact_error(exc),
            }
            results.append(failure)

    status_snapshot = write_status(payload.get("status_path"), run_id, results, dry_run)
    return {
        "ok": ok,
        "script": SCRIPT_NAME,
        "run_id": run_id,
        "dry_run": dry_run,
        "results": results,
        "status": status_snapshot,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", help="JSON input file; defaults to stdin")
    parser.add_argument("--dry-run", action="store_true", help="plan without mutating docs")
    parser.add_argument("--pretty", action="store_true", help="pretty-print JSON output")
    args = parser.parse_args()

    try:
        payload = read_payload(args.input)
        result = run(payload, args.dry_run)
    except Exception as exc:  # noqa: BLE001 - stable JSON output for orchestration
        result = {
            "ok": False,
            "script": SCRIPT_NAME,
            "dry_run": args.dry_run,
            "error": compact_error(exc),
        }
        emit(result, args.pretty)
        return 1

    emit(result, args.pretty)
    return 0 if result.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
