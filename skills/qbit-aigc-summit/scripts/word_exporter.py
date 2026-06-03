#!/usr/bin/env python3
"""Export selected Lark documents to Word files with stable filenames."""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import tempfile
from urllib.parse import urlparse
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import state_store


SCRIPT_NAME = "word_exporter"
DEFAULT_TEMPLATE = "{index:02d}_{name}.docx"


class ExportError(Exception):
    """A recoverable export failure with item context."""


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def read_payload(path: str | None) -> dict[str, Any]:
    if path:
        with open(path, "r", encoding="utf-8") as handle:
            return json.load(handle)
    raw = sys.stdin.read()
    if not raw.strip():
        raise ExportError("missing JSON input on stdin; pass --input or pipe JSON")
    return json.loads(raw)


def emit(payload: dict[str, Any], pretty: bool) -> None:
    kwargs = {"ensure_ascii": False}
    if pretty:
        kwargs["indent"] = 2
    print(json.dumps(payload, **kwargs))


def compact_error(exc: BaseException) -> str:
    text = str(exc).strip()
    return text if len(text) <= 2000 else text[:1997] + "..."


def run_json(argv: list[str], keep_raw: bool = False) -> dict[str, Any]:
    completed = subprocess.run(argv, text=True, capture_output=True, check=False)
    command_result = {
        "argv": argv,
        "returncode": completed.returncode,
        "stdout": completed.stdout,
        "stderr": completed.stderr,
    }
    if completed.returncode != 0:
        raise ExportError(
            f"command failed({completed.returncode}): {' '.join(argv)}\n{completed.stderr.strip()}"
        )
    if not completed.stdout.strip():
        return {"_command": command_result}
    try:
        parsed = json.loads(completed.stdout)
    except json.JSONDecodeError:
        parsed = {"raw_stdout": completed.stdout}
    if isinstance(parsed, dict):
        parsed.setdefault("_command", command_result if keep_raw else {"argv": argv})
        return parsed
    return {"value": parsed, "_command": command_result if keep_raw else {"argv": argv}}


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
        raise ExportError(f"status_path must contain a JSON object: {path}")
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
        if item_status == "exported":
            updates.append(
                state_store.update_status(
                    path=status_path,
                    item_id=str(item["id"]),
                    module=SCRIPT_NAME,
                    status="已导出Word",
                    message="已按命名规范导出Word",
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
                    error=str(item.get("error") or "export failed"),
                    retry_reason="检查文档token、导出权限、输出目录和命名模板后重试",
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


def item_id(document: dict[str, Any], index: int) -> str:
    return str(
        document.get("id")
        or document.get("section_id")
        or document.get("speaker")
        or document.get("title")
        or f"doc_{index:02d}"
    )


def normalize_documents(payload: dict[str, Any]) -> list[dict[str, Any]]:
    documents = payload.get("documents") or payload.get("items")
    if not isinstance(documents, list):
        raise ExportError("input must include documents or items as a list")
    return [document for document in documents if isinstance(document, dict)]


def sanitize_filename(value: str, fallback: str) -> str:
    cleaned = re.sub(r"[\\/:*?\"<>|\r\n\t]+", "_", value).strip(" ._")
    cleaned = re.sub(r"\s+", "_", cleaned)
    return cleaned or fallback


def ensure_docx(filename: str) -> str:
    return filename if filename.lower().endswith(".docx") else f"{filename}.docx"


def format_filename(
    payload: dict[str, Any],
    document: dict[str, Any],
    index: int,
    resolved_title: str | None,
) -> str:
    explicit = document.get("file_name") or document.get("filename")
    if explicit:
        return ensure_docx(sanitize_filename(str(explicit), f"doc_{index:02d}"))

    name = (
        document.get("export_name")
        or document.get("name")
        or document.get("speaker")
        or resolved_title
        or document.get("title")
        or item_id(document, index)
    )
    context = {
        "index": index,
        "id": item_id(document, index),
        "name": sanitize_filename(str(name), f"doc_{index:02d}"),
        "title": sanitize_filename(str(resolved_title or document.get("title") or name), f"doc_{index:02d}"),
        "speaker": sanitize_filename(str(document.get("speaker") or name), f"doc_{index:02d}"),
        "kind": sanitize_filename(str(document.get("kind") or document.get("target_kind") or "doc"), "doc"),
        "date": str(payload.get("date") or datetime.now().strftime("%Y%m%d")),
    }
    template = str(payload.get("filename_template") or DEFAULT_TEMPLATE)
    try:
        filename = template.format(**context)
    except (KeyError, ValueError) as exc:
        raise ExportError(f"invalid filename_template: {exc}") from exc
    return ensure_docx(sanitize_filename(filename, f"doc_{index:02d}.docx"))


def inspect_doc(document: dict[str, Any], as_identity: str | None) -> dict[str, Any] | None:
    url = document.get("doc") or document.get("url") or document.get("target_doc")
    if not url:
        return None
    argv = ["lark-cli", "drive", "+inspect", "--url", str(url)]
    if as_identity:
        argv.extend(["--as", as_identity])
    return run_json(argv)


def token_from_url(value: str | None) -> str | None:
    if not value:
        return None
    parsed = urlparse(value)
    parts = [part for part in parsed.path.split("/") if part]
    for marker in ("docx", "doc"):
        if marker in parts:
            index = parts.index(marker)
            if index + 1 < len(parts):
                return parts[index + 1]
    return None


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


def resolved_field(
    document: dict[str, Any],
    inspected: dict[str, Any] | None,
    field: str,
    aliases: tuple[str, ...],
) -> Any:
    for key in aliases:
        if document.get(key):
            return document[key]
    if inspected:
        for key in (field, *aliases):
            value = recursive_find(inspected, key)
            if value:
                return value
    return None


def build_export_argv(
    token: str,
    doc_type: str,
    output_dir: str,
    file_name: str,
    as_identity: str | None,
    overwrite: bool,
    dry_run: bool,
) -> list[str]:
    argv = [
        "lark-cli",
        "drive",
        "+export",
        "--token",
        token,
        "--doc-type",
        doc_type,
        "--file-extension",
        "docx",
        "--output-dir",
        output_dir,
        "--file-name",
        file_name,
    ]
    if overwrite:
        argv.append("--overwrite")
    if as_identity:
        argv.extend(["--as", as_identity])
    if dry_run:
        argv.append("--dry-run")
    return argv


def export_one(
    payload: dict[str, Any],
    document: dict[str, Any],
    index: int,
    as_identity: str | None,
    dry_run: bool,
) -> dict[str, Any]:
    doc_id = item_id(document, index)
    inspected = None
    if (
        not dry_run
        and (not document.get("token") or not document.get("title") or not document.get("doc_type"))
    ):
        inspected = inspect_doc(document, as_identity)

    token = resolved_field(document, inspected, "token", ("token", "file_token", "obj_token"))
    needs_inspect = False
    if not token and dry_run:
        token = token_from_url(
            str(document.get("doc") or document.get("url") or document.get("target_doc") or "")
        )
        if not token:
            token = "<inspect-required>"
            needs_inspect = True
    if not token:
        raise ExportError("document is missing token and could not be inspected from doc/url")

    doc_type = str(
        resolved_field(document, inspected, "type", ("doc_type", "type", "obj_type")) or "docx"
    ).lower()
    if doc_type not in {"doc", "docx"}:
        raise ExportError(f"Word export expects doc/docx source, got {doc_type}")

    title = resolved_field(document, inspected, "title", ("title",))
    output_dir = str(document.get("output_dir") or payload.get("output_dir") or ".")
    file_name = format_filename(payload, document, index, str(title) if title else None)
    argv = build_export_argv(
        token=str(token),
        doc_type=doc_type,
        output_dir=output_dir,
        file_name=file_name,
        as_identity=as_identity,
        overwrite=bool(document.get("overwrite", payload.get("overwrite", False))),
        dry_run=dry_run,
    )
    base = {
        "id": doc_id,
        "status": "planned" if dry_run else "exported",
        "updated_at": utc_now(),
        "token": str(token),
        "doc_type": doc_type,
        "file_name": file_name,
        "output_dir": output_dir,
        "output_path": str(Path(output_dir) / file_name),
        "command": argv,
    }
    if needs_inspect:
        base["needs_inspect"] = True
    if dry_run:
        return base

    result = run_json(argv)
    saved_path = recursive_find(result, "saved_path") or recursive_find(result, "output_path")
    if saved_path:
        base["output_path"] = str(saved_path)
    base["export"] = result
    return base


def run(payload: dict[str, Any], cli_dry_run: bool) -> dict[str, Any]:
    dry_run = bool(cli_dry_run or payload.get("dry_run"))
    run_id = str(payload.get("run_id") or f"{SCRIPT_NAME}_{utc_now()}")
    as_identity = payload.get("as") or payload.get("identity")
    documents = normalize_documents(payload)
    results: list[dict[str, Any]] = []
    ok = True

    for index, document in enumerate(documents, start=1):
        doc_id = item_id(document, index)
        try:
            results.append(export_one(payload, document, index, as_identity, dry_run))
        except Exception as exc:  # noqa: BLE001 - script must report item-level failures
            ok = False
            results.append(
                {
                    "id": doc_id,
                    "status": "failed",
                    "updated_at": utc_now(),
                    "error": compact_error(exc),
                }
            )

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
    parser.add_argument("--dry-run", action="store_true", help="plan without exporting files")
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
