#!/usr/bin/env python3
"""Create the initial total draft skeleton, then person docs after confirmation."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path
from string import Template
from typing import Any

import state_store


SCRIPT_DIR = Path(__file__).resolve().parent
SKILL_DIR = SCRIPT_DIR.parent
TEMPLATE_DIR = SKILL_DIR / "templates"


def load_json_input(value: str) -> dict[str, Any]:
    if value == "-":
        raw = sys.stdin.read()
    elif value.startswith("@"):
        raw = Path(value[1:]).read_text(encoding="utf-8")
    else:
        raw = value
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ValueError(f"invalid JSON input: {exc}") from exc
    if not isinstance(data, dict):
        raise ValueError("input must be a JSON object")
    return data


def render_template(name: str, values: dict[str, Any]) -> str:
    path = TEMPLATE_DIR / name
    template = Template(path.read_text(encoding="utf-8"))
    safe_values = {key: "" if value is None else str(value) for key, value in values.items()}
    return template.safe_substitute(safe_values)


def xml_escape(value: Any) -> str:
    text = "" if value is None else str(value)
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def no_zh_en_space(value: Any) -> str:
    text = "" if value is None else str(value)
    text = text.replace("\\1\\2", "")
    cleaned = []
    for index, char in enumerate(text):
        if char != " ":
            cleaned.append(char)
            continue
        prev_char = text[index - 1] if index > 0 else ""
        next_char = text[index + 1] if index + 1 < len(text) else ""
        prev_is_cjk = "\u4e00" <= prev_char <= "\u9fff"
        next_is_cjk = "\u4e00" <= next_char <= "\u9fff"
        prev_is_ascii = prev_char.isascii() and prev_char.isalnum()
        next_is_ascii = next_char.isascii() and next_char.isalnum()
        if (prev_is_cjk and next_is_ascii) or (prev_is_ascii and next_is_cjk):
            continue
        cleaned.append(char)
    return "".join(cleaned)


def extract_topic(person: dict[str, Any]) -> str:
    topic = str(person.get("topic", "")).strip()
    if topic:
        return topic
    source_label = str(person.get("source_label", "")).strip()
    marker = "主题："
    if marker not in source_label:
        return ""
    tail = source_label.split(marker, 1)[1]
    return tail.split("；", 1)[0].strip()


def normalize_people(data: dict[str, Any]) -> list[dict[str, Any]]:
    people = data.get("people")
    if not isinstance(people, list) or not people:
        raise ValueError("input.people must be a non-empty array")
    normalized: list[dict[str, Any]] = []
    for index, person in enumerate(people, start=1):
        if not isinstance(person, dict):
            raise ValueError(f"input.people[{index - 1}] must be an object")
        name = str(person.get("name", "")).strip()
        if not name:
            raise ValueError(f"input.people[{index - 1}].name is required")
        person_id = str(person.get("id") or person.get("slug") or name).strip()
        normalized.append(
            {
                "id": person_id,
                "name": no_zh_en_space(name),
                "title": no_zh_en_space(str(person.get("title", "")).strip()),
                "role": no_zh_en_space(str(person.get("role", "")).strip()),
                "owner": no_zh_en_space(str(person.get("owner", "")).strip()),
                "source_label": no_zh_en_space(str(person.get("source_label", "")).strip()),
                "topic": no_zh_en_space(str(person.get("topic", "")).strip()),
            }
        )
    return normalized


def build_total_xml(data: dict[str, Any], people: list[dict[str, Any]]) -> str:
    sections = []
    for person in people:
        sections.append(
            render_template(
                "total_draft_section.xml",
                {
                    "person_id": xml_escape(person["id"]),
                    "person_name": xml_escape(person["name"]),
                    "person_title": xml_escape(person["title"]),
                    "person_role": xml_escape(person["role"]),
                    "source_label": xml_escape(person["source_label"]),
                    "person_topic": xml_escape(extract_topic(person)),
                },
            )
        )
    body = "\n".join(sections)
    title = xml_escape(data.get("total_title", "AIGC峰会总结总稿"))
    return (
        f"<doc>\n<title>{title}</title>\n"
        "<h2>标题：</h2>\n"
        "<p>1、</p>\n<p>2、</p>\n<p>3、</p>\n<p>4、</p>\n<p>5、</p>\n"
        "<p></p>\n"
        "<p>##### 组委会 发自 凹非寺 &lt;br&gt;量子位 | 公众号QbitAI</p>\n"
        "<p></p>\n"
        "<p>大会开篇导语待补充。</p>\n"
        "<p></p>\n"
        f"{body}\n"
        "<h1>头图</h1>\n<h2>封面</h2>\n<p></p>\n<h2>素材</h2>\n<p></p>\n<h2>PSD</h2>\n<p></p>\n"
        "</doc>\n"
    )


def build_person_xml(person: dict[str, Any], confirmed: bool = False) -> str:
    template = "confirmed_person_doc.xml" if confirmed else "empty_person_doc.xml"
    return render_template(
        template,
        {
            "person_id": xml_escape(person["id"]),
            "person_name": xml_escape(person["name"]),
            "person_title": xml_escape(person["title"]),
            "person_role": xml_escape(person["role"]),
            "source_label": xml_escape(person["source_label"]),
            "person_topic": xml_escape(extract_topic(person)),
        },
    )


def write_local_artifacts(
    *,
    output_dir: Path,
    data: dict[str, Any],
    people: list[dict[str, Any]],
    create_person_docs: bool,
    dry_run: bool,
) -> dict[str, Any]:
    total_xml = build_total_xml(data, people)
    person_docs = (
        {person["id"]: build_person_xml(person, confirmed=False) for person in people}
        if create_person_docs
        else {}
    )
    total_path = output_dir / "total_draft.xml"
    person_dir = output_dir / "people"
    person_paths = {
        person_id: person_dir / f"{safe_filename(person_id)}.xml" for person_id in person_docs
    }
    if not dry_run:
        output_dir.mkdir(parents=True, exist_ok=True)
        total_path.write_text(total_xml, encoding="utf-8")
        if person_docs:
            person_dir.mkdir(parents=True, exist_ok=True)
        for person_id, xml in person_docs.items():
            person_paths[person_id].write_text(xml, encoding="utf-8")
    return {
        "total_xml_path": str(total_path),
        "person_xml_paths": {person_id: str(path) for person_id, path in person_paths.items()},
    }


def safe_filename(value: str) -> str:
    keep = []
    for char in value:
        if char.isalnum() or char in ("-", "_"):
            keep.append(char)
        else:
            keep.append("_")
    return "".join(keep).strip("_") or "person"


def run_lark_create(expected_title: str, xml_path: str, dry_run: bool) -> dict[str, Any]:
    cmd = [
        "lark-cli",
        "docs",
        "+create",
        "--api-version",
        "v2",
        "--doc-format",
        "xml",
        "--content",
        f"@{xml_path}",
    ]
    if dry_run:
        return {"command": cmd, "expected_title": expected_title, "skipped": True}
    if not shutil.which("lark-cli"):
        raise RuntimeError("lark-cli not found in PATH")
    completed = subprocess.run(cmd, check=False, capture_output=True, text=True)
    if completed.returncode != 0:
        raise RuntimeError(completed.stderr.strip() or completed.stdout.strip() or "lark-cli create failed")
    try:
        parsed = json.loads(completed.stdout)
    except json.JSONDecodeError:
        parsed = {"stdout": completed.stdout.strip()}
    parsed["command"] = cmd
    parsed["expected_title"] = expected_title
    return parsed


def create_docs(
    *,
    data: dict[str, Any],
    people: list[dict[str, Any]],
    artifacts: dict[str, Any],
    create_person_docs: bool,
    dry_run: bool,
) -> dict[str, Any]:
    if not data.get("create_feishu_docs"):
        return {"enabled": False}
    total_title = str(data.get("total_title", "AIGC峰会总结总稿"))
    created: dict[str, Any] = {
        "enabled": True,
        "total": run_lark_create(total_title, artifacts["total_xml_path"], dry_run),
        "people": {},
    }
    if not create_person_docs:
        created["people_skipped"] = "等待总稿骨架人工确认后再创建单人/圆桌文档"
        return created
    for person in people:
        title = str(data.get("person_title_pattern", "${name}｜AIGC峰会单人稿")).replace(
            "${name}", person["name"]
        )
        created["people"][person["id"]] = run_lark_create(
            title,
            artifacts["person_xml_paths"][person["id"]],
            dry_run,
        )
    return created


def update_success_state(
    *,
    state_path: Path,
    assignment_id: str,
    people: list[dict[str, Any]],
    artifacts: dict[str, Any],
    created_docs: dict[str, Any],
    create_person_docs: bool,
    dry_run: bool,
) -> list[dict[str, Any]]:
    events = []
    events.append(
        state_store.update_status(
            path=state_path,
            item_id=assignment_id,
            module="assignment_doc_builder",
            status="已建总稿骨架",
            message="总稿骨架已生成",
            data={"artifacts": artifacts, "created_docs": created_docs},
            dry_run=dry_run,
        )["event"]
    )
    if not create_person_docs:
        events.append(
            state_store.update_status(
                path=state_path,
                item_id=assignment_id,
                module="assignment_doc_builder",
                status="待骨架确认",
                message="总稿骨架待人工确认，确认后再创建单人/圆桌文档",
                data={"artifacts": artifacts, "created_docs": created_docs},
                dry_run=dry_run,
            )["event"]
        )
        return events
    for person in people:
        events.append(
            state_store.update_status(
                path=state_path,
                item_id=person["id"],
                module="assignment_doc_builder",
                status="已建单人空文档",
                message="单人空文档已生成",
                data={
                    "person": person,
                    "artifact": artifacts["person_xml_paths"][person["id"]],
                    "created_doc": created_docs.get("people", {}).get(person["id"]),
                },
                dry_run=dry_run,
            )["event"]
        )
    return events


def write_failure_state(
    *,
    state_path: Path | None,
    assignment_id: str,
    error: Exception,
    dry_run: bool,
) -> None:
    if state_path is None:
        return
    try:
        state_store.update_status(
            path=state_path,
            item_id=assignment_id,
            module="assignment_doc_builder",
            status=state_store.FAILURE_STATUS,
            error=str(error),
            retry_reason="修正输入、模板或飞书创建环境后重试建稿",
            dry_run=dry_run,
        )
    except Exception as state_error:
        print(
            json.dumps(
                {
                    "ok": False,
                    "error": str(error),
                    "state_error": str(state_error),
                },
                ensure_ascii=False,
                indent=2,
            ),
            file=sys.stderr,
        )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Build total draft skeleton; create person docs only after skeleton confirmation."
    )
    parser.add_argument("--input", required=True, help="JSON object, @file, or - for stdin.")
    parser.add_argument("--state", required=True, help="Path to shared JSON state.")
    parser.add_argument("--output-dir", required=True, help="Directory for generated XML artifacts.")
    parser.add_argument("--assignment-id", help="Override input.assignment_id.")
    parser.add_argument(
        "--create-person-docs",
        action="store_true",
        help="Create per-person and roundtable docs after the total skeleton has been manually confirmed.",
    )
    parser.add_argument("--dry-run", action="store_true", help="Print planned writes and commands.")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    state_path = Path(args.state).expanduser()
    assignment_id = args.assignment_id or "assignment"
    try:
        data = load_json_input(args.input)
        assignment_id = args.assignment_id or str(data.get("assignment_id") or "assignment")
        people = normalize_people(data)
        artifacts = write_local_artifacts(
            output_dir=Path(args.output_dir).expanduser(),
            data=data,
            people=people,
            create_person_docs=args.create_person_docs,
            dry_run=args.dry_run,
        )
        created_docs = create_docs(
            data=data,
            people=people,
            artifacts=artifacts,
            create_person_docs=args.create_person_docs,
            dry_run=args.dry_run,
        )
        events = update_success_state(
            state_path=state_path,
            assignment_id=assignment_id,
            people=people,
            artifacts=artifacts,
            created_docs=created_docs,
            create_person_docs=args.create_person_docs,
            dry_run=args.dry_run,
        )
        result = {
            "ok": True,
            "dry_run": args.dry_run,
            "assignment_id": assignment_id,
            "artifacts": artifacts,
            "created_docs": created_docs,
            "state_events": events,
        }
        print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
        return 0
    except Exception as exc:
        write_failure_state(
            state_path=state_path,
            assignment_id=assignment_id,
            error=exc,
            dry_run=args.dry_run,
        )
        print(json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False, indent=2), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
