#!/usr/bin/env python3
"""End-to-end viewpoint writer for the AIGC summit SOP.

The script owns the mechanical workflow:
1. collect transcript/minutes artifacts;
2. filter source material by speaker mapping;
3. produce five viewpoint bullets;
4. locate the target section in the summit master doc;
5. write the bullets back to that section;
6. append a status row.

Use --llm-command for the judgment-heavy drafting step. The command receives a
prompt on stdin and must return either JSON {"points": ["..."]} or five lines.
Without --llm-command the script falls back to a deterministic extractor so the
pipeline remains runnable during setup and tests.
"""

from __future__ import annotations

import argparse
import datetime as dt
import html
import json
import os
import re
import shlex
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable
from xml.etree import ElementTree as ET

import state_store


STYLE_RULES = """写五条观点精华提炼，要求：
- 少写PR，优先写判断、约束、方法、分歧和非共识结论。
- 贴近讲者原意，不抽象改写成口号。
- 保留关键术语、英文缩写、产品/技术名和鲜活比喻。
- 中文和English之间不要加空格。
- 禁用该类二元对举句式。
- 每条是一句话，可用分号承接逻辑，避免空泛赞美。
- 输出JSON：{"points":["第一条","第二条","第三条","第四条","第五条"]}。
"""

VIEWPOINT_HEADINGS = ("观点精华提炼", "观点精炼", "观点提炼")
BAN_PATTERNS = (
    re.compile(r"\u4e0d\u662f[^。；\n]{0,80}\u800c\u662f"),
    re.compile(r"[\u4e00-\u9fff]\s+[A-Za-z0-9]"),
    re.compile(r"[A-Za-z0-9]\s+[\u4e00-\u9fff]"),
)
FILLER_WORDS = {
    "然后",
    "其实",
    "就是",
    "这个",
    "那个",
    "我们",
    "他们",
    "一个",
    "以及",
    "所以",
    "因为",
    "如果",
    "可能",
    "觉得",
    "可以",
}
INSIGHT_HINTS = (
    "窗口",
    "瓶颈",
    "约束",
    "问题",
    "核心",
    "关键",
    "差异",
    "范式",
    "能力",
    "成本",
    "效率",
    "信任",
    "关系",
    "协议",
    "流程",
    "原子",
    "推理",
    "训练",
    "数据",
    "边缘",
    "垂直",
    "可解释",
    "可追溯",
    "可验证",
    "Agent",
    "AI",
    "Coding",
    "planner",
    "builder",
    "reviewer",
)
PR_HINTS = ("领先", "赋能", "生态伙伴", "重磅", "发布", "亮相", "携手", "打造", "全面升级")


@dataclass(frozen=True)
class Utterance:
    speaker_key: str
    speaker_name: str
    text: str
    raw: str


@dataclass(frozen=True)
class SourceBundle:
    transcript: str
    artifacts: dict[str, Any]
    source_label: str


@dataclass(frozen=True)
class TargetLocation:
    section_block_id: str
    section_title: str
    mode: str
    anchor_block_id: str


class ViewpointError(RuntimeError):
    pass


def run_cmd(args: list[str], *, input_text: str | None = None, dry_run: bool = False) -> str:
    printable = " ".join(shlex.quote(part) for part in args)
    if dry_run:
        print(f"[dry-run] {printable}", file=sys.stderr)
        return "{}"
    proc = subprocess.run(
        args,
        input=input_text,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if proc.returncode != 0:
        raise ViewpointError(f"Command failed: {printable}\n{proc.stderr.strip()}")
    return proc.stdout


def load_text_arg(value: str | None) -> str:
    if not value:
        return ""
    if value.startswith("@"):
        return Path(value[1:]).read_text(encoding="utf-8")
    return value


def load_json_arg(value: str | None) -> Any:
    text = load_text_arg(value)
    if not text:
        return None
    return json.loads(text)


def parse_speaker_map(raw: str | None) -> dict[str, str]:
    if not raw:
        return {}
    text = load_text_arg(raw).strip()
    if not text:
        return {}
    if text.startswith("{"):
        data = json.loads(text)
        return {normalize_speaker_key(str(k)): str(v).strip() for k, v in data.items()}

    mapping: dict[str, str] = {}
    for piece in re.split(r"[,，;\n]+", text):
        piece = piece.strip()
        if not piece:
            continue
        match = re.match(r"(?:说话人|speaker)?\s*([A-Za-z0-9_-]+)\s*(?:=|:|：|是)\s*(.+)", piece, re.I)
        if not match:
            raise ViewpointError(f"Cannot parse speaker mapping item: {piece}")
        key, name = match.groups()
        mapping[normalize_speaker_key(key)] = name.strip()
    return mapping


def normalize_speaker_key(raw: str) -> str:
    text = raw.strip()
    text = re.sub(r"^(说话人|speaker)\s*", "", text, flags=re.I)
    return text.strip()


def collect_source(args: argparse.Namespace) -> SourceBundle:
    artifacts: dict[str, Any] = {}
    source_parts: list[str] = []
    transcript_chunks: list[str] = []

    if args.transcript_file:
        path = Path(args.transcript_file)
        transcript_chunks.append(path.read_text(encoding="utf-8"))
        source_parts.append(str(path))

    id_flags = [
        ("--minute-tokens", args.minute_token),
        ("--meeting-ids", args.meeting_id),
        ("--calendar-event-ids", args.calendar_event_id),
    ]
    provided = [(flag, value) for flag, value in id_flags if value]
    if len(provided) > 1:
        raise ViewpointError("Use only one of --minute-token, --meeting-id, --calendar-event-id.")
    if provided:
        flag, value = provided[0]
        output_dir = args.output_dir or str(Path.cwd() / "minutes")
        cmd = ["lark-cli", "vc", "+notes", flag, value, "--format", "json"]
        if flag == "--minute-tokens":
            cmd.extend(["--output-dir", output_dir, "--overwrite"])
        raw = run_cmd(cmd, dry_run=args.dry_run)
        artifacts = parse_cli_json(raw)
        transcript_chunks.extend(fetch_transcripts_from_notes(artifacts, args.dry_run))
        source_parts.append(f"{flag}={value}")

    if args.note_doc:
        transcript_chunks.append(fetch_doc_text(args.note_doc, "markdown", args.dry_run))
        source_parts.append(f"note_doc={args.note_doc}")

    if args.verbatim_doc:
        transcript_chunks.append(fetch_doc_text(args.verbatim_doc, "markdown", args.dry_run))
        source_parts.append(f"verbatim_doc={args.verbatim_doc}")

    transcript = "\n\n".join(chunk.strip() for chunk in transcript_chunks if chunk.strip())
    if not transcript:
        raise ViewpointError("No transcript or minutes content found.")
    return SourceBundle(transcript=transcript, artifacts=artifacts, source_label=";".join(source_parts))


def parse_cli_json(raw: str) -> dict[str, Any]:
    raw = raw.strip()
    if not raw:
        return {}
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        start = raw.find("{")
        end = raw.rfind("}")
        if start >= 0 and end > start:
            return json.loads(raw[start : end + 1])
        raise


def fetch_transcripts_from_notes(data: dict[str, Any], dry_run: bool) -> list[str]:
    chunks: list[str] = []
    for path in find_values(data, "transcript_file"):
        if isinstance(path, str) and Path(path).exists():
            chunks.append(Path(path).read_text(encoding="utf-8"))

    for token in find_values(data, "verbatim_doc_token"):
        if isinstance(token, str) and token.strip():
            chunks.append(fetch_doc_text(token, "markdown", dry_run))

    for key in ("summary", "chapters"):
        values = find_values(data, key)
        if values:
            chunks.append(json.dumps(values, ensure_ascii=False, indent=2))
    return chunks


def find_values(value: Any, key: str) -> list[Any]:
    found: list[Any] = []
    if isinstance(value, dict):
        for item_key, item_value in value.items():
            if item_key == key:
                found.append(item_value)
            found.extend(find_values(item_value, key))
    elif isinstance(value, list):
        for item in value:
            found.extend(find_values(item, key))
    return found


def fetch_doc_text(doc: str, doc_format: str, dry_run: bool, extra: list[str] | None = None) -> str:
    cmd = [
        "lark-cli",
        "docs",
        "+fetch",
        "--api-version",
        "v2",
        "--doc",
        doc,
        "--doc-format",
        doc_format,
        "--format",
        "json",
    ]
    if extra:
        cmd.extend(extra)
    # Dry runs still need to read the target structure so write commands can be
    # previewed against real block IDs.
    raw = run_cmd(cmd, dry_run=False)
    data = parse_cli_json(raw)
    return str(data.get("data", {}).get("document", {}).get("content", raw))


def parse_utterances(transcript: str, speaker_map: dict[str, str]) -> list[Utterance]:
    utterances: list[Utterance] = []
    current_key = ""
    current_name = ""
    current_lines: list[str] = []

    line_pattern = re.compile(
        r"^\s*(?:\[?\d{1,2}:\d{2}(?::\d{2})?\]?\s*)?"
        r"(?:(说话人|speaker)\s*)?([A-Za-z0-9_-]+)"
        r"(?:\s*[\]\)]?\s*(?:[:：]|-)\s*|\s+)"
        r"(.+)$",
        re.I,
    )

    def flush() -> None:
        nonlocal current_key, current_name, current_lines
        text = "\n".join(current_lines).strip()
        if current_key and text:
            utterances.append(
                Utterance(
                    speaker_key=current_key,
                    speaker_name=current_name or speaker_map.get(current_key, current_key),
                    text=text,
                    raw=text,
                )
            )
        current_key = ""
        current_name = ""
        current_lines = []

    for line in transcript.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        match = line_pattern.match(stripped)
        if match:
            _, raw_key, text = match.groups()
            key = normalize_speaker_key(raw_key)
            if speaker_map and key in speaker_map:
                flush()
                current_key = key
                current_name = speaker_map[key]
                current_lines = [text.strip()]
                continue
            if not speaker_map:
                flush()
                current_key = key
                current_name = key
                current_lines = [text.strip()]
                continue
        if current_key:
            current_lines.append(stripped)
    flush()

    if speaker_map:
        selected = [item for item in utterances if item.speaker_key in speaker_map]
        if selected:
            return selected
    if not utterances:
        return [Utterance("all", "all", transcript, transcript)]
    return utterances


def build_prompt(utterances: list[Utterance], source: SourceBundle, speaker_map: dict[str, str]) -> str:
    speaker_label = "、".join(dict.fromkeys(item.speaker_name for item in utterances))
    source_text = "\n\n".join(f"【{item.speaker_name}】{item.text}" for item in utterances)
    if len(source_text) > 24000:
        source_text = source_text[:24000] + "\n\n[TRUNCATED]"
    artifacts = json.dumps(source.artifacts, ensure_ascii=False)[:6000] if source.artifacts else ""
    return (
        f"{STYLE_RULES}\n"
        f"speaker mapping:{json.dumps(speaker_map, ensure_ascii=False)}\n"
        f"目标讲者:{speaker_label}\n\n"
        f"妙记产物摘要:{artifacts}\n\n"
        f"逐字稿:\n{source_text}\n"
    )


def generate_points(
    utterances: list[Utterance],
    source: SourceBundle,
    speaker_map: dict[str, str],
    args: argparse.Namespace,
) -> list[str]:
    manual = load_json_arg(args.points_json)
    if manual:
        points = manual.get("points", manual) if isinstance(manual, dict) else manual
        return normalize_points(points)

    prompt = build_prompt(utterances, source, speaker_map)
    if args.prompt_out:
        Path(args.prompt_out).write_text(prompt, encoding="utf-8")

    if args.llm_command:
        raw = run_cmd(shlex.split(args.llm_command), input_text=prompt, dry_run=args.dry_run)
        return normalize_points(parse_points_output(raw))

    return normalize_points(heuristic_points(utterances))


def parse_points_output(raw: str) -> list[str]:
    text = raw.strip()
    try:
        data = json.loads(text)
        points = data.get("points", data) if isinstance(data, dict) else data
        return [str(item).strip() for item in points]
    except json.JSONDecodeError:
        pass
    lines = [re.sub(r"^\s*(?:[-*]|\d+[.、])\s*", "", line).strip() for line in text.splitlines()]
    return [line for line in lines if line]


def heuristic_points(utterances: list[Utterance]) -> list[str]:
    sentences: list[str] = []
    for item in utterances:
        chunks = re.split(r"(?<=[。！？!?])\s*|\n+", item.text)
        for chunk in chunks:
            cleaned = cleanup_sentence(chunk)
            if len(cleaned) >= 18:
                sentences.append(cleaned)

    ranked = sorted(
        dict.fromkeys(sentences),
        key=lambda item: (score_sentence(item), len(item)),
        reverse=True,
    )
    points: list[str] = []
    for sentence in ranked:
        if len(points) >= 5:
            break
        if any(similar(sentence, old) for old in points):
            continue
        points.append(sentence)

    if len(points) < 5:
        raise ViewpointError(
            f"Only found {len(points)} usable viewpoint candidates. "
            "Use --llm-command or provide --points-json after human review."
        )
    return points


def cleanup_sentence(text: str) -> str:
    text = compact_mixed_spacing(text.strip())
    text = re.sub(r"^(嗯|啊|呃|这个|那个|然后|其实|就是)+", "", text)
    text = re.sub(r"[，,；;：:]+$", "。", text)
    if text and text[-1] not in "。！？!?":
        text += "。"
    return text


def compact_mixed_spacing(text: str) -> str:
    text = re.sub(r"(?<=[\u4e00-\u9fff])\s+(?=[A-Za-z0-9])", "", text)
    text = re.sub(r"(?<=[A-Za-z0-9])\s+(?=[\u4e00-\u9fff])", "", text)
    text = re.sub(r"(?<=[\u4e00-\u9fff])\s+(?=[\u4e00-\u9fff])", "", text)
    text = re.sub(r"[ \t]{2,}", " ", text)
    return text


def score_sentence(text: str) -> int:
    score = 0
    score += sum(5 for hint in INSIGHT_HINTS if hint in text)
    score -= sum(4 for hint in PR_HINTS if hint in text)
    score -= sum(1 for word in FILLER_WORDS if word in text)
    if 28 <= len(text) <= 110:
        score += 8
    if "？" in text or "?" in text:
        score += 2
    if re.search(r"[A-Za-z][A-Za-z0-9_-]{1,}", text):
        score += 3
    return score


def similar(a: str, b: str) -> bool:
    a_terms = set(re.findall(r"[\u4e00-\u9fff]{2,}|[A-Za-z][A-Za-z0-9_-]+", a))
    b_terms = set(re.findall(r"[\u4e00-\u9fff]{2,}|[A-Za-z][A-Za-z0-9_-]+", b))
    if not a_terms or not b_terms:
        return False
    return len(a_terms & b_terms) / max(1, min(len(a_terms), len(b_terms))) > 0.55


def normalize_points(points: Iterable[Any]) -> list[str]:
    cleaned: list[str] = []
    for item in points:
        text = cleanup_sentence(str(item))
        if text:
            cleaned.append(text)
    if len(cleaned) != 5:
        raise ViewpointError(f"Expected exactly five points, got {len(cleaned)}.")
    errors = validate_points(cleaned)
    if errors:
        raise ViewpointError("Point validation failed:\n" + "\n".join(f"- {item}" for item in errors))
    return cleaned


def validate_points(points: list[str]) -> list[str]:
    errors: list[str] = []
    for index, point in enumerate(points, start=1):
        if len(point) < 18:
            errors.append(f"point {index} is too short")
        for pattern in BAN_PATTERNS:
            if pattern.search(point):
                errors.append(f"point {index} violates style rule: {point}")
                break
    return errors


def locate_target(args: argparse.Namespace) -> TargetLocation:
    if args.target_block_id:
        section_xml = fetch_doc_text(
            args.target_doc,
            "xml",
            args.dry_run,
            ["--scope", "section", "--start-block-id", args.target_block_id, "--detail", "with-ids"],
        )
        mode, anchor = find_viewpoint_anchor(section_xml, args.target_block_id)
        return TargetLocation(
            section_block_id=args.target_block_id,
            section_title=args.target_section_keyword or args.target_block_id,
            mode=mode,
            anchor_block_id=anchor,
        )
    if not args.target_section_keyword:
        raise ViewpointError("Set --target-section-keyword or --target-block-id.")

    outline = fetch_doc_text(
        args.target_doc,
        "xml",
        args.dry_run,
        ["--scope", "outline", "--max-depth", "5", "--detail", "with-ids"],
    )
    headings = parse_heading_blocks(outline)
    matches = [item for item in headings if args.target_section_keyword in item[1]]
    if not matches:
        raise ViewpointError(f"Cannot find target section keyword: {args.target_section_keyword}")
    section_id, section_title, _ = matches[0]

    section_xml = fetch_doc_text(
        args.target_doc,
        "xml",
        args.dry_run,
        ["--scope", "section", "--start-block-id", section_id, "--detail", "with-ids"],
    )
    mode, anchor = find_viewpoint_anchor(section_xml, section_id)
    return TargetLocation(section_block_id=section_id, section_title=section_title, mode=mode, anchor_block_id=anchor)


def parse_heading_blocks(xml_text: str) -> list[tuple[str, str, str]]:
    blocks = parse_xml_children(xml_text)
    headings: list[tuple[str, str, str]] = []
    for element in walk_elements(blocks):
        tag = strip_ns(element.tag)
        if re.fullmatch(r"h[1-6]", tag):
            block_id = element.attrib.get("id") or element.attrib.get("block-id")
            if block_id:
                headings.append((block_id, element_text(element), tag))
    return headings


def find_viewpoint_anchor(section_xml: str, fallback_section_id: str) -> tuple[str, str]:
    children = parse_xml_children(section_xml)
    top = unwrap_fragment(children)
    for index, element in enumerate(top):
        text = element_text(element)
        block_id = element.attrib.get("id") or element.attrib.get("block-id")
        if not block_id:
            continue
        if any(heading in text for heading in VIEWPOINT_HEADINGS):
            for next_element in top[index + 1 :]:
                next_id = next_element.attrib.get("id") or next_element.attrib.get("block-id")
                if strip_ns(next_element.tag) in {"ul", "ol"}:
                    if next_id:
                        return "replace", next_id
                    item_ids = [
                        item.attrib.get("id") or item.attrib.get("block-id")
                        for item in list(next_element)
                        if strip_ns(item.tag) == "li"
                    ]
                    item_ids = [item_id for item_id in item_ids if item_id]
                    if len(item_ids) >= 5:
                        return "replace_list_items", ",".join(item_ids[:5])
                    continue
                if not next_id:
                    continue
                if strip_ns(next_element.tag).startswith("h"):
                    break
            return "insert_after", block_id
    return "insert_after", fallback_section_id


def unwrap_fragment(children: list[ET.Element]) -> list[ET.Element]:
    if len(children) == 1 and strip_ns(children[0].tag) == "fragment":
        return list(children[0])
    return children


def parse_xml_children(xml_text: str) -> list[ET.Element]:
    text = xml_text.strip()
    text = re.sub(r"<\?xml[^>]*>", "", text)
    wrapped = f"<root>{text}</root>"
    try:
        return list(ET.fromstring(wrapped))
    except ET.ParseError:
        safe = re.sub(r"&(?!amp;|lt;|gt;|quot;|apos;|#\d+;)", "&amp;", text)
        return list(ET.fromstring(f"<root>{safe}</root>"))


def walk_elements(elements: Iterable[ET.Element]) -> Iterable[ET.Element]:
    for element in elements:
        yield element
        yield from walk_elements(list(element))


def strip_ns(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def element_text(element: ET.Element) -> str:
    return "".join(element.itertext()).strip()


def points_to_xml(points: list[str], include_heading: bool) -> str:
    items = "".join(f"<li>{html.escape(point)}</li>" for point in points)
    body = f"<ul>{items}</ul>"
    if include_heading:
        return f"<h4>观点精华提炼</h4>{body}"
    return body


def write_points(args: argparse.Namespace, target: TargetLocation, points: list[str]) -> dict[str, Any]:
    if target.mode == "replace_list_items":
        results = []
        block_ids = target.anchor_block_id.split(",")
        if len(block_ids) != len(points):
            raise ViewpointError("replacement list item count does not match point count")
        for block_id, point in zip(block_ids, points):
            cmd = [
                "lark-cli",
                "docs",
                "+update",
                "--api-version",
                "v2",
                "--doc",
                args.target_doc,
                "--command",
                "block_replace",
                "--block-id",
                block_id,
                "--content",
                f"<li>{html.escape(point)}</li>",
            ]
            raw = run_cmd(cmd, dry_run=args.dry_run)
            results.append(parse_cli_json(raw))
        return {"ok": True, "mode": target.mode, "results": results}
    content = points_to_xml(points, include_heading=target.mode == "insert_after")
    command = "block_replace" if target.mode == "replace" else "block_insert_after"
    cmd = [
        "lark-cli",
        "docs",
        "+update",
        "--api-version",
        "v2",
        "--doc",
        args.target_doc,
        "--command",
        command,
        "--block-id",
        target.anchor_block_id,
        "--content",
        content,
    ]
    raw = run_cmd(cmd, dry_run=args.dry_run)
    return parse_cli_json(raw)


def update_json_state(args: argparse.Namespace, target: TargetLocation, points: list[str], source: SourceBundle) -> dict[str, Any] | None:
    if not args.state:
        return None
    item_id = args.item_id or args.target_section_keyword or target.section_title
    return state_store.update_status(
        path=Path(args.state).expanduser(),
        item_id=item_id,
        module="viewpoint_writer",
        status="待人工确认",
        message="观点已写入总稿，等待人工确认",
        data={
            "target_doc": args.target_doc,
            "target_section": target.section_title,
            "target_block_id": target.anchor_block_id,
            "source": source.source_label,
            "point_count": len(points),
            "points": points,
        },
        dry_run=args.dry_run,
    )


def append_status_sheet(args: argparse.Namespace, target: TargetLocation, points: list[str], source: SourceBundle) -> dict[str, Any] | None:
    if not (args.status_sheet_url or args.status_spreadsheet_token):
        return None

    row = [
        dt.datetime.now().isoformat(timespec="seconds"),
        args.target_section_keyword or target.section_title,
        target.section_title,
        args.target_doc,
        "待人工确认",
        len(points),
        source.source_label,
        "\n".join(points),
    ]
    values = json.dumps([row], ensure_ascii=False)
    cmd = ["lark-cli", "sheets", "+append", "--values", values]
    if args.status_sheet_url:
        cmd.extend(["--url", args.status_sheet_url])
    else:
        cmd.extend(["--spreadsheet-token", args.status_spreadsheet_token])
    if args.status_sheet_id:
        cmd.extend(["--sheet-id", args.status_sheet_id])
    if args.status_range:
        cmd.extend(["--range", args.status_range])
    raw = run_cmd(cmd, dry_run=args.dry_run)
    return parse_cli_json(raw)


def update_status(args: argparse.Namespace, target: TargetLocation, points: list[str], source: SourceBundle) -> dict[str, Any]:
    if args.skip_status_update:
        return {"skipped": True}
    if not (args.state or args.status_sheet_url or args.status_spreadsheet_token):
        raise ViewpointError("Pass --state for shared JSON state or a status sheet target.")
    json_state = update_json_state(args, target, points, source)
    sheet = append_status_sheet(args, target, points, source)
    return {"json_state": json_state, "sheet": sheet}


def update_failure_status(args: argparse.Namespace, error: Exception) -> dict[str, Any] | None:
    if args.skip_status_update or not args.state:
        return None
    item_id = args.item_id or args.target_section_keyword or args.target_doc
    return state_store.update_status(
        path=Path(args.state).expanduser(),
        item_id=item_id,
        module="viewpoint_writer",
        status=state_store.FAILURE_STATUS,
        error=str(error),
        retry_reason="检查逐字稿来源、speaker mapping、目标章节关键词和Feishu权限后重试",
        dry_run=args.dry_run,
    )


def write_audit(args: argparse.Namespace, payload: dict[str, Any]) -> None:
    if not args.audit_file:
        return
    path = Path(args.audit_file)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Write five viewpoint bullets into a Feishu summit master doc.")
    source = parser.add_argument_group("source")
    source.add_argument("--transcript-file", help="Local transcript.txt path.")
    source.add_argument("--minute-token", help="Feishu Minutes token; calls lark-cli vc +notes.")
    source.add_argument("--meeting-id", help="Feishu VC meeting id; calls lark-cli vc +notes.")
    source.add_argument("--calendar-event-id", help="Calendar event id; calls lark-cli vc +notes.")
    source.add_argument("--note-doc", help="AI notes doc token or URL.")
    source.add_argument("--verbatim-doc", help="Verbatim doc token or URL.")
    source.add_argument("--output-dir", help="Directory for vc +notes artifacts.")

    draft = parser.add_argument_group("draft")
    draft.add_argument("--speaker-map", required=True, help='Mapping like "3=庄明浩,4=冯雷" or @mapping.json.')
    draft.add_argument("--llm-command", help="Command that receives the drafting prompt on stdin and returns JSON points.")
    draft.add_argument("--points-json", help='Manual points JSON or @file, shape {"points":[...five items...]}.')
    draft.add_argument("--prompt-out", help="Write the drafting prompt to this path for human review.")

    target = parser.add_argument_group("target")
    target.add_argument("--target-doc", required=True, help="Summit master doc token or URL.")
    target.add_argument("--target-section-keyword", help="Keyword used to pick the target section from outline.")
    target.add_argument("--target-block-id", help="Exact block id for viewpoint list replacement.")

    status = parser.add_argument_group("status")
    status.add_argument("--state", help="Shared JSON state path.")
    status.add_argument("--item-id", help="Stable state item id. Defaults to section keyword or section title.")
    status.add_argument("--status-sheet-url", help="Status sheet URL.")
    status.add_argument("--status-spreadsheet-token", help="Status spreadsheet token.")
    status.add_argument("--status-sheet-id", help="Status worksheet id.")
    status.add_argument("--status-range", help="Append range, e.g. SheetId!A1.")
    status.add_argument("--skip-status-update", action="store_true", help="Allow local dry runs without touching status sheet.")

    parser.add_argument("--audit-file", help="Write a JSON audit file.")
    parser.add_argument("--dry-run", action="store_true", help="Print write commands without executing them.")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_arg_parser()
    args = parser.parse_args(argv)
    try:
        speaker_map = parse_speaker_map(args.speaker_map)
        source = collect_source(args)
        utterances = parse_utterances(source.transcript, speaker_map)
        points = generate_points(utterances, source, speaker_map, args)
        target = locate_target(args)
        write_result = write_points(args, target, points)
        status_result = update_status(args, target, points, source)
        payload = {
            "ok": True,
            "points": points,
            "target": target.__dict__,
            "write_result": write_result,
            "status_result": status_result,
            "source": source.source_label,
        }
        write_audit(args, payload)
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 0
    except Exception as exc:
        try:
            failure = update_failure_status(args, exc)
            if failure:
                print(json.dumps({"ok": False, "failure_status": failure}, ensure_ascii=False, indent=2), file=sys.stderr)
        except Exception as status_exc:  # noqa: BLE001
            print(f"STATUS_ERROR: {status_exc}", file=sys.stderr)
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
