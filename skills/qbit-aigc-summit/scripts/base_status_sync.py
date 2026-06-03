#!/usr/bin/env python3
"""Sync SOP state into a Feishu Base status table."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

import state_store


FIELDS = [
    "对象",
    "类型",
    "状态",
    "负责人",
    "角色",
    "主题",
    "文档链接",
    "总稿链接",
    "更新时间",
    "备注",
]


def load_assignment_input(path: Path | None) -> dict[str, dict[str, Any]]:
    if path is None or not path.exists():
        return {}
    data = json.loads(path.read_text(encoding="utf-8"))
    people = data.get("people", [])
    if not isinstance(people, list):
        return {}
    return {str(person.get("id")): person for person in people if isinstance(person, dict)}


def infer_type(item_id: str, item: dict[str, Any], person: dict[str, Any] | None) -> str:
    if item_id == "aigc-summit-2026":
        return "总控"
    if item_id == "roundtable":
        return "圆桌稿"
    if person and person.get("role") == "圆桌对话":
        return "圆桌稿"
    return "单人稿"


def item_name(item_id: str, item: dict[str, Any], person: dict[str, Any] | None) -> str:
    data = item.get("data", {})
    if isinstance(data, dict) and data.get("name"):
        return str(data["name"])
    if person and person.get("name"):
        return str(person["name"])
    if item_id == "aigc-summit-2026":
        return "2026AIGC产业峰会总结"
    return item_id


def build_rows(
    *,
    state: dict[str, Any],
    people_by_id: dict[str, dict[str, Any]],
    total_doc_url: str,
) -> list[list[Any]]:
    rows: list[list[Any]] = []
    items = state.get("items", {})
    roundtable_item = items.get("roundtable", {})
    roundtable_data = roundtable_item.get("data", {}) if isinstance(roundtable_item, dict) else {}
    roundtable_status = (
        str(roundtable_item.get("status", "")) if isinstance(roundtable_item, dict) else ""
    )
    roundtable_url = (
        str(roundtable_data.get("doc_url", "")) if isinstance(roundtable_data, dict) else ""
    )
    for item_id, item in items.items():
        if not isinstance(item, dict):
            continue
        if item_id == "recvjX8EzQeiD0":
            continue
        person = people_by_id.get(item_id)
        data = item.get("data", {})
        if not isinstance(data, dict):
            data = {}
        status = str(item.get("status", ""))
        role = str(person.get("role", "")) if person else ""
        if item_id == "roundtable":
            role = "圆桌对话"
        topic = str(person.get("topic", "")) if person else ""
        owner = str(person.get("owner", "")) if person else ""
        doc_url = str(data.get("doc_url") or data.get("roundtable_doc_url") or "")
        if person and person.get("role") == "圆桌对话" and item_id != "roundtable":
            doc_url = roundtable_url
            if roundtable_status:
                status = roundtable_status
        if item_id == "aigc-summit-2026":
            doc_url = str(data.get("total_doc_url") or total_doc_url)
        note = ""
        if item.get("error"):
            note = str(item["error"])
        elif item_id == "aigc-summit-2026":
            note = f"拆分数量:{data.get('split_count', '')}"
        rows.append(
            [
                item_name(item_id, item, person),
                infer_type(item_id, item, person),
                status,
                owner,
                role,
                topic,
                doc_url,
                total_doc_url,
                str(item.get("updated_at", ""))[:19].replace("T", " "),
                note,
            ]
        )
    rows.sort(key=lambda row: (row[1] != "总控", row[1] == "圆桌稿", row[0]))
    return rows


def run_lark_batch_create(
    *,
    base_token: str,
    table_id: str,
    rows: list[list[Any]],
    dry_run: bool,
) -> dict[str, Any]:
    payload = {"fields": FIELDS, "rows": rows}
    if dry_run:
        return {"ok": True, "dry_run": True, "payload": payload}
    cmd = [
        "lark-cli",
        "base",
        "+record-batch-create",
        "--base-token",
        base_token,
        "--table-id",
        table_id,
        "--json",
        json.dumps(payload, ensure_ascii=False),
        "--as",
        "user",
    ]
    completed = subprocess.run(cmd, check=False, capture_output=True, text=True)
    if completed.returncode != 0:
        raise RuntimeError(completed.stderr.strip() or completed.stdout.strip())
    try:
        return json.loads(completed.stdout)
    except json.JSONDecodeError:
        return {"ok": True, "stdout": completed.stdout}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Sync SOP state into Feishu Base.")
    parser.add_argument("--state", required=True, help="Path to the internal state source.")
    parser.add_argument("--assignment-input", help="Path to assignment input JSON.")
    parser.add_argument("--base-token", required=True, help="Target Base token.")
    parser.add_argument("--table-id", required=True, help="Target table id or name.")
    parser.add_argument("--total-doc-url", required=True, help="Total draft URL.")
    parser.add_argument("--dry-run", action="store_true", help="Print planned rows without writing.")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        state = state_store.load_state(Path(args.state).expanduser())
        people_by_id = load_assignment_input(
            Path(args.assignment_input).expanduser() if args.assignment_input else None
        )
        rows = build_rows(
            state=state,
            people_by_id=people_by_id,
            total_doc_url=args.total_doc_url,
        )
        result = run_lark_batch_create(
            base_token=args.base_token,
            table_id=args.table_id,
            rows=rows,
            dry_run=args.dry_run,
        )
        print(
            json.dumps(
                {"ok": True, "row_count": len(rows), "sync_result": result},
                ensure_ascii=False,
                indent=2,
            )
        )
        return 0
    except Exception as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False, indent=2), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
