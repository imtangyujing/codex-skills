#!/usr/bin/env python3
"""Export a Feishu outline doc and place its body into the local Word template."""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
import tempfile
import zipfile
from copy import deepcopy
from pathlib import Path
from xml.etree import ElementTree as ET


NS = {
    "a": "http://schemas.openxmlformats.org/drawingml/2006/main",
    "mc": "http://schemas.openxmlformats.org/markup-compatibility/2006",
    "pic": "http://schemas.openxmlformats.org/drawingml/2006/picture",
    "wp": "http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing",
    "wp14": "http://schemas.microsoft.com/office/word/2010/wordprocessingDrawing",
    "w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main",
    "w10": "urn:schemas-microsoft-com:office:word",
    "w14": "http://schemas.microsoft.com/office/word/2010/wordml",
    "w15": "http://schemas.microsoft.com/office/word/2012/wordml",
    "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
    "v": "urn:schemas-microsoft-com:vml",
    "ct": "http://schemas.openxmlformats.org/package/2006/content-types",
    "pr": "http://schemas.openxmlformats.org/package/2006/relationships",
    "dc": "http://purl.org/dc/elements/1.1/",
}
for prefix, uri in NS.items():
    ET.register_namespace(prefix if prefix not in {"ct", "pr"} else "", uri)

REL_NS = f"{{{NS['pr']}}}"
W_NS = f"{{{NS['w']}}}"
R_ID = f"{{{NS['r']}}}id"
R_EMBED = f"{{{NS['r']}}}embed"
R_LINK = f"{{{NS['r']}}}link"
RELATIONSHIP_ATTRS = {R_ID, R_EMBED, R_LINK}


SKILL_DIR = Path(__file__).resolve().parents[1]
DEFAULT_TEMPLATE = SKILL_DIR / "assets/qbit-template.docx"
DEFAULT_OUTPUT_DIR = Path.home() / "Downloads"


def run_json(argv: list[str], cwd: Path | None = None) -> dict:
    proc = subprocess.run(argv, cwd=cwd, text=True, capture_output=True)
    if proc.returncode != 0:
        raise RuntimeError((proc.stderr or proc.stdout).strip())
    text = proc.stdout.strip()
    start = text.find("{")
    if start < 0:
        raise RuntimeError(f"Command did not return JSON: {' '.join(argv)}")
    return json.loads(text[start:])


def safe_filename(name: str) -> str:
    cleaned = re.sub(r'[\\/:*?"<>|]+', "-", name).strip()
    return cleaned or "飞书提纲"


def inspect_doc(url: str) -> dict:
    data = run_json(["lark-cli", "drive", "+inspect", "--as", "user", "--url", url])
    if not data.get("ok"):
        raise RuntimeError(json.dumps(data, ensure_ascii=False, indent=2))
    item = data["data"]
    if item.get("type") != "docx":
        raise RuntimeError(f"当前只支持导出docx，实际类型是{item.get('type')}")
    return item


def export_docx(token: str, title: str, workdir: Path) -> Path:
    filename = f"{safe_filename(title)}-飞书导出.docx"
    data = run_json(
        [
            "lark-cli",
            "drive",
            "+export",
            "--as",
            "user",
            "--token",
            token,
            "--doc-type",
            "docx",
            "--file-extension",
            "docx",
            "--file-name",
            filename,
            "--output-dir",
            ".",
            "--overwrite",
        ],
        cwd=workdir,
    )
    if data.get("ok"):
        return Path(data["data"]["saved_path"])
    hint = data.get("error", {}).get("hint", "")
    match = re.search(r'--file-token "([^"]+)".*--file-name "([^"]+)"', hint)
    if not match:
        raise RuntimeError(json.dumps(data, ensure_ascii=False, indent=2))
    file_token, file_name = match.groups()
    dl = run_json(
        [
            "lark-cli",
            "drive",
            "+export-download",
            "--as",
            "user",
            "--file-token",
            file_token,
            "--file-name",
            file_name,
            "--output-dir",
            ".",
            "--overwrite",
        ],
        cwd=workdir,
    )
    if not dl.get("ok"):
        raise RuntimeError(json.dumps(dl, ensure_ascii=False, indent=2))
    return Path(dl["data"]["saved_path"])


def unzip_docx(path: Path, dest: Path) -> None:
    with zipfile.ZipFile(path) as zf:
        zf.extractall(dest)


def zip_docx(src: Path, dest: Path) -> None:
    with zipfile.ZipFile(dest, "w", zipfile.ZIP_DEFLATED) as zf:
        for path in sorted(src.rglob("*")):
            if path.is_file():
                zf.write(path, path.relative_to(src).as_posix())


def rel_ids(root: ET.Element) -> set[str]:
    return {item.attrib.get("Id", "") for item in root.findall(f"{REL_NS}Relationship")}


def next_rid(used: set[str]) -> str:
    i = 1
    while f"rId{i}" in used:
        i += 1
    rid = f"rId{i}"
    used.add(rid)
    return rid


def unique_word_target(template_dir: Path, target: str) -> str:
    if target.startswith("..") or re.match(r"^[a-z]+:", target):
        return target
    target_path = Path(target)
    dst_path = template_dir / "word" / target_path
    if not dst_path.exists():
        return target

    stem = target_path.stem
    suffix = target_path.suffix
    parent = target_path.parent
    i = 1
    while True:
        candidate = parent / f"{stem}_src{i}{suffix}"
        if not (template_dir / "word" / candidate).exists():
            return candidate.as_posix()
        i += 1


def merge_relationships(template_dir: Path, source_dir: Path, source_body: ET.Element) -> None:
    src_rels_path = source_dir / "word/_rels/document.xml.rels"
    dst_rels_path = template_dir / "word/_rels/document.xml.rels"
    if not src_rels_path.exists():
        return

    src_root = ET.parse(src_rels_path).getroot()
    dst_tree = ET.parse(dst_rels_path)
    dst_root = dst_tree.getroot()
    used = rel_ids(dst_root)
    rid_map: dict[str, str] = {}

    for rel in src_root.findall(f"{REL_NS}Relationship"):
        target = rel.attrib.get("Target", "")
        rel_type = rel.attrib.get("Type", "")
        if rel_type.endswith("/header") or rel_type.endswith("/footer"):
            continue
        old_id = rel.attrib.get("Id")
        if not old_id:
            continue
        new_id = next_rid(used)
        rid_map[old_id] = new_id
        new_rel = deepcopy(rel)
        new_rel.set("Id", new_id)
        new_target = unique_word_target(template_dir, target)
        new_rel.set("Target", new_target)
        dst_root.append(new_rel)
        if not target.startswith("..") and not re.match(r"^[a-z]+:", target):
            src_target = source_dir / "word" / target
            dst_target = template_dir / "word" / new_target
            if src_target.exists():
                dst_target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src_target, dst_target)

    for elem in source_body.iter():
        for key, value in list(elem.attrib.items()):
            if key in RELATIONSHIP_ATTRS and value in rid_map:
                elem.set(key, rid_map[value])

    dst_tree.write(dst_rels_path, encoding="UTF-8", xml_declaration=True)


def copy_source_word_parts(template_dir: Path, source_dir: Path) -> None:
    for rel_path in source_dir.rglob("*"):
        if not rel_path.is_file():
            continue
        rel = rel_path.relative_to(source_dir).as_posix()
        if rel in {
            "word/document.xml",
            "word/_rels/document.xml.rels",
        }:
            continue
        if re.match(r"word/(header|footer)\d+\.xml$", rel):
            continue
        if re.match(r"word/_rels/(header|footer)\d+\.xml\.rels$", rel):
            continue
        if rel.startswith("docProps/"):
            continue
        if rel.startswith("word/media/"):
            continue
        if rel.startswith("word/") and (
            rel.endswith(".xml")
            or rel.startswith("word/embeddings/")
            or rel.startswith("word/charts/")
            or rel.startswith("word/diagrams/")
        ):
            dest = template_dir / rel
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(rel_path, dest)


def merge_content_types(template_dir: Path, source_dir: Path) -> None:
    src_path = source_dir / "[Content_Types].xml"
    dst_path = template_dir / "[Content_Types].xml"
    src_root = ET.parse(src_path).getroot()
    dst_tree = ET.parse(dst_path)
    dst_root = dst_tree.getroot()
    existing = {
        (child.tag, child.attrib.get("PartName"), child.attrib.get("Extension"))
        for child in dst_root
    }
    for child in src_root:
        key = (child.tag, child.attrib.get("PartName"), child.attrib.get("Extension"))
        if key not in existing:
            dst_root.append(deepcopy(child))
            existing.add(key)
    dst_tree.write(dst_path, encoding="UTF-8", xml_declaration=True)


def set_core_title(template_dir: Path, title: str) -> None:
    path = template_dir / "docProps/core.xml"
    if not path.exists():
        return
    tree = ET.parse(path)
    root = tree.getroot()
    title_node = root.find(f"{{{NS['dc']}}}title")
    if title_node is not None:
        title_node.text = title
    tree.write(path, encoding="UTF-8", xml_declaration=True)


def center_banner_title(body: ET.Element) -> None:
    for para in body.findall(f"{W_NS}p"):
        text = "".join(node.text or "" for node in para.iter(f"{W_NS}t")).strip()
        if not text:
            continue
        ppr = para.find(f"{W_NS}pPr")
        if ppr is None:
            ppr = ET.Element(f"{W_NS}pPr")
            para.insert(0, ppr)
        jc = ppr.find(f"{W_NS}jc")
        if jc is None:
            jc = ET.SubElement(ppr, f"{W_NS}jc")
        jc.set(f"{W_NS}val", "center")
        ind = ppr.find(f"{W_NS}ind")
        if ind is None:
            ind = ET.SubElement(ppr, f"{W_NS}ind")
        for key in ("left", "right", "firstLine", "hanging"):
            ind.attrib.pop(f"{W_NS}{key}", None)
        ind.set(f"{W_NS}left", "0")
        ind.set(f"{W_NS}right", "0")
        return


def paragraph_text(elem: ET.Element) -> str:
    return "".join(node.text or "" for node in elem.iter(f"{W_NS}t")).strip()


def drop_from_heading(body: ET.Element, heading: str) -> None:
    if not heading:
        return
    children = list(body)
    drop_idx: int | None = None
    for i, child in enumerate(children):
        if child.tag == f"{W_NS}p" and heading in paragraph_text(child):
            drop_idx = i
    if drop_idx is None:
        raise RuntimeError(f"未找到要删除的章节标题：{heading}")
    for child in children[drop_idx:]:
        if child.tag != f"{W_NS}sectPr":
            body.remove(child)


def strip_generated_content_notice(body: ET.Element) -> None:
    notice_patterns = (
        "内容由AI生成，请谨慎参考",
        "内容由 AI 生成，请谨慎参考",
    )
    for child in list(body):
        text = paragraph_text(child).replace(" ", "")
        if any(pattern.replace(" ", "") in text for pattern in notice_patterns):
            if child.tag != f"{W_NS}sectPr":
                body.remove(child)


def relationship_ids(elem: ET.Element) -> set[str]:
    ids: set[str] = set()
    for node in elem.iter():
        for key, value in node.attrib.items():
            if key in RELATIONSHIP_ATTRS and value:
                ids.add(value)
    return ids


def prune_unused_document_relationships(template_dir: Path, body: ET.Element) -> None:
    rels_path = template_dir / "word/_rels/document.xml.rels"
    if not rels_path.exists():
        return
    used = relationship_ids(body)
    tree = ET.parse(rels_path)
    root = tree.getroot()
    for rel in list(root.findall(f"{REL_NS}Relationship")):
        rel_id = rel.attrib.get("Id")
        rel_type = rel.attrib.get("Type", "")
        if rel_type.endswith("/image") and rel_id not in used:
            root.remove(rel)
    tree.write(rels_path, encoding="UTF-8", xml_declaration=True)


def prune_unreferenced_media(template_dir: Path) -> None:
    referenced: set[str] = set()
    rels_dir = template_dir / "word/_rels"
    for rels_path in rels_dir.glob("*.rels"):
        root = ET.parse(rels_path).getroot()
        base = rels_path.name.removesuffix(".xml.rels")
        for rel in root.findall(f"{REL_NS}Relationship"):
            if not rel.attrib.get("Type", "").endswith("/image"):
                continue
            target = rel.attrib.get("Target", "")
            if target.startswith("..") or re.match(r"^[a-z]+:", target):
                continue
            if base == "document":
                referenced.add((template_dir / "word" / target).resolve().as_posix())
            else:
                referenced.add((template_dir / "word" / target).resolve().as_posix())

    media_dir = template_dir / "word/media"
    if not media_dir.exists():
        return
    for media_path in media_dir.iterdir():
        if media_path.is_file() and media_path.resolve().as_posix() not in referenced:
            media_path.unlink()


def normalize_xml_parts(template_dir: Path) -> None:
    for path in template_dir.rglob("*"):
        if not path.is_file() or path.suffix not in {".xml", ".rels"}:
            continue
        tree = ET.parse(path)
        tree.write(path, encoding="UTF-8", xml_declaration=True)


def merge_docx(
    template: Path,
    source: Path,
    output: Path,
    title: str,
    drop_heading: str | None = None,
) -> None:
    with tempfile.TemporaryDirectory() as tmp:
        tmp_dir = Path(tmp)
        template_dir = tmp_dir / "template"
        source_dir = tmp_dir / "source"
        unzip_docx(template, template_dir)
        unzip_docx(source, source_dir)

        dst_doc_path = template_dir / "word/document.xml"
        src_doc_path = source_dir / "word/document.xml"
        dst_tree = ET.parse(dst_doc_path)
        src_tree = ET.parse(src_doc_path)
        dst_body = dst_tree.getroot().find(f"{W_NS}body")
        src_body = src_tree.getroot().find(f"{W_NS}body")
        if dst_body is None or src_body is None:
            raise RuntimeError("Word文档缺少body")

        merge_relationships(template_dir, source_dir, src_body)
        copy_source_word_parts(template_dir, source_dir)
        merge_content_types(template_dir, source_dir)
        set_core_title(template_dir, title)

        dst_sect = dst_body.find(f"{W_NS}sectPr")
        for child in list(dst_body):
            dst_body.remove(child)
        for child in list(src_body):
            if child.tag != f"{W_NS}sectPr":
                dst_body.append(deepcopy(child))
        strip_generated_content_notice(dst_body)
        if drop_heading:
            drop_from_heading(dst_body, drop_heading)
        prune_unused_document_relationships(template_dir, dst_body)
        prune_unreferenced_media(template_dir)
        if dst_sect is not None:
            dst_body.append(dst_sect)
        center_banner_title(dst_body)

        dst_tree.write(dst_doc_path, encoding="UTF-8", xml_declaration=True)
        normalize_xml_parts(template_dir)
        output.parent.mkdir(parents=True, exist_ok=True)
        zip_docx(template_dir, output)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("url", help="Feishu wiki/docx URL")
    parser.add_argument("--template", type=Path, default=DEFAULT_TEMPLATE)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--name", help="Output filename without .docx")
    parser.add_argument("--keep-export", action="store_true", help="Keep the raw Feishu export")
    parser.add_argument(
        "--drop-from-heading",
        help="Drop the last section whose paragraph text contains this heading, through the end of the body",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    item = inspect_doc(args.url)
    title = item["title"]
    output_name = safe_filename(args.name or title)
    output = args.output_dir / f"{output_name}.docx"

    with tempfile.TemporaryDirectory(prefix="feishu-outline-") as tmp:
        workdir = Path(tmp)
        exported = export_docx(item["token"], title, workdir)
        merge_docx(
            args.template,
            exported,
            output,
            title,
            args.drop_from_heading,
        )
        if args.keep_export:
            shutil.copy2(exported, args.output_dir / exported.name)

    print(json.dumps({"ok": True, "title": title, "output": str(output)}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
