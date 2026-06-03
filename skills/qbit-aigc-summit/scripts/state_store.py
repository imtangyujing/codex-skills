#!/usr/bin/env python3
"""Shared JSON state store for the AIGC summit SOP."""

from __future__ import annotations

import argparse
import copy
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


STATUS_FLOW = [
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
]

FAILURE_STATUS = "失败"
VALID_STATUSES = set(STATUS_FLOW + [FAILURE_STATUS])


def now_iso() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def load_state(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"schema_version": 1, "items": {}, "events": []}
    try:
        with path.open("r", encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError as exc:
        raise ValueError(f"state file is not valid JSON: {path}: {exc}") from exc
    if not isinstance(data, dict):
        raise ValueError("state root must be a JSON object")
    data.setdefault("schema_version", 1)
    data.setdefault("items", {})
    data.setdefault("events", [])
    if not isinstance(data["items"], dict):
        raise ValueError("state.items must be a JSON object")
    if not isinstance(data["events"], list):
        raise ValueError("state.events must be a JSON array")
    return data


def save_state(path: Path, state: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = path.with_suffix(path.suffix + ".tmp")
    with tmp_path.open("w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2, sort_keys=True)
        f.write("\n")
    tmp_path.replace(path)


def parse_json_arg(value: str | None) -> dict[str, Any]:
    if not value:
        return {}
    if value == "-":
        raw = sys.stdin.read()
    elif value.startswith("@"):
        raw = Path(value[1:]).read_text(encoding="utf-8")
    else:
        raw = value
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ValueError(f"invalid JSON input: {exc}") from exc
    if not isinstance(parsed, dict):
        raise ValueError("JSON input must be an object")
    return parsed


def ensure_item(state: dict[str, Any], item_id: str) -> dict[str, Any]:
    items = state.setdefault("items", {})
    item = items.setdefault(item_id, {})
    item.setdefault("id", item_id)
    item.setdefault("status", "待建稿")
    item.setdefault("history", [])
    return item


def append_event(
    state: dict[str, Any],
    *,
    item_id: str,
    module: str,
    status: str,
    message: str | None = None,
    error: str | None = None,
    retry_reason: str | None = None,
    data: dict[str, Any] | None = None,
) -> dict[str, Any]:
    if status not in VALID_STATUSES:
        raise ValueError(f"invalid status: {status}")
    if status == FAILURE_STATUS and (not error or not retry_reason):
        raise ValueError("failure updates require error and retry_reason")

    event = {
        "at": now_iso(),
        "item_id": item_id,
        "module": module,
        "status": status,
    }
    if message:
        event["message"] = message
    if error:
        event["error"] = error
    if retry_reason:
        event["retry_reason"] = retry_reason
    if data:
        event["data"] = data

    item = ensure_item(state, item_id)
    item.update(
        {
            "status": status,
            "updated_at": event["at"],
            "updated_by": module,
        }
    )
    if error:
        item["error"] = error
    else:
        item.pop("error", None)
    if retry_reason:
        item["retry_reason"] = retry_reason
    elif status != FAILURE_STATUS:
        item.pop("retry_reason", None)
    if data:
        item.setdefault("data", {}).update(data)
    item.setdefault("history", []).append(event)
    state.setdefault("events", []).append(event)
    return event


def update_status(
    *,
    path: Path,
    item_id: str,
    module: str,
    status: str,
    message: str | None = None,
    error: str | None = None,
    retry_reason: str | None = None,
    data: dict[str, Any] | None = None,
    dry_run: bool = False,
) -> dict[str, Any]:
    state = load_state(path)
    before = copy.deepcopy(state)
    event = append_event(
        state,
        item_id=item_id,
        module=module,
        status=status,
        message=message,
        error=error,
        retry_reason=retry_reason,
        data=data,
    )
    if not dry_run:
        save_state(path, state)
    return {
        "ok": True,
        "dry_run": dry_run,
        "state_path": str(path),
        "event": event,
        "item": state["items"][item_id],
        "would_write": before != state,
    }


def get_item(path: Path, item_id: str | None = None) -> dict[str, Any]:
    state = load_state(path)
    if item_id:
        return {"ok": True, "item": state.get("items", {}).get(item_id)}
    return {"ok": True, "state": state}


def validate_state(path: Path) -> dict[str, Any]:
    state = load_state(path)
    invalid: list[dict[str, str]] = []
    for item_id, item in state.get("items", {}).items():
        status = item.get("status")
        if status not in VALID_STATUSES:
            invalid.append({"item_id": item_id, "status": str(status)})
    return {
        "ok": not invalid,
        "state_path": str(path),
        "valid_statuses": STATUS_FLOW + [FAILURE_STATUS],
        "invalid_items": invalid,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Read and update the AIGC summit SOP JSON state.")
    parser.add_argument("--state", required=True, help="Path to the shared JSON state file.")
    parser.add_argument("--dry-run", action="store_true", help="Return the planned mutation without writing.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    update = subparsers.add_parser("update", help="Write a normal status update.")
    update.add_argument("--item-id", required=True, help="Assignment/person/section id.")
    update.add_argument("--module", required=True, help="Name of the caller module.")
    update.add_argument("--status", required=True, choices=STATUS_FLOW, help="Next status.")
    update.add_argument("--message", help="Short human readable note.")
    update.add_argument("--data", help="JSON object, @file, or - for stdin.")

    fail = subparsers.add_parser("fail", help="Write a failure update.")
    fail.add_argument("--item-id", required=True, help="Assignment/person/section id.")
    fail.add_argument("--module", required=True, help="Name of the caller module.")
    fail.add_argument("--error", required=True, help="Error message.")
    fail.add_argument("--retry-reason", required=True, help="What must change before retry.")
    fail.add_argument("--message", help="Short human readable note.")
    fail.add_argument("--data", help="JSON object, @file, or - for stdin.")

    get = subparsers.add_parser("get", help="Read the full state or one item.")
    get.add_argument("--item-id", help="Assignment/person/section id.")

    subparsers.add_parser("validate", help="Validate the state schema and statuses.")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    path = Path(args.state).expanduser()
    try:
        if args.command == "update":
            result = update_status(
                path=path,
                item_id=args.item_id,
                module=args.module,
                status=args.status,
                message=args.message,
                data=parse_json_arg(args.data),
                dry_run=args.dry_run,
            )
        elif args.command == "fail":
            result = update_status(
                path=path,
                item_id=args.item_id,
                module=args.module,
                status=FAILURE_STATUS,
                message=args.message,
                error=args.error,
                retry_reason=args.retry_reason,
                data=parse_json_arg(args.data),
                dry_run=args.dry_run,
            )
        elif args.command == "get":
            result = get_item(path, args.item_id)
        elif args.command == "validate":
            result = validate_state(path)
        else:
            parser.error(f"unknown command: {args.command}")
    except Exception as exc:
        result = {"ok": False, "error": str(exc)}
        print(json.dumps(result, ensure_ascii=False, indent=2), file=sys.stderr)
        return 1
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if result.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
