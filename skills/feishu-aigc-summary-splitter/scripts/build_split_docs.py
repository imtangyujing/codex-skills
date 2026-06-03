#!/usr/bin/env python3
"""Create Feishu docx drafts from a JSON spec.

Input:
  build_split_docs.py spec.json [--make-editable]

The spec must contain:
  {"docs": [{"title": "...", "owner": "...", "xml": "<h2>...</h2>"}]}

Each document is created with lark-cli docs +create --api-version v2 --as user
--doc-format xml. With --make-editable, the script also sets tenant-editable
link permissions. The script retries gently on Feishu frequency limits and
prints a JSON array with title, owner, url, doc_id, and optional editable.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from pathlib import Path


def create_doc(title: str, owner: str, xml: str) -> dict:
    content = f"<title>{escape_xml(title)}</title>{xml}"
    cmd = [
        "lark-cli",
        "docs",
        "+create",
        "--api-version",
        "v2",
        "--as",
        "user",
        "--doc-format",
        "xml",
        "--content",
        content,
    ]

    last_output = ""
    for attempt in range(5):
        proc = subprocess.run(cmd, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        last_output = proc.stdout + proc.stderr
        if proc.returncode == 0:
            payload = json.loads(proc.stdout)
            doc = payload["data"]["document"]
            return {
                "title": title,
                "owner": owner,
                "url": doc["url"],
                "doc_id": doc["document_id"],
            }

        if "frequency limit" in last_output or "rate_limit" in last_output:
            time.sleep(8 + attempt * 4)
            continue

        raise RuntimeError(last_output)

    raise RuntimeError(f"rate limit persisted for {title}: {last_output}")


def make_editable(doc_id: str) -> bool:
    cmd = [
        "lark-cli",
        "drive",
        "permission.public",
        "patch",
        "--as",
        "user",
        "--yes",
        "--params",
        json.dumps({"token": doc_id, "type": "docx"}, ensure_ascii=False),
        "--data",
        json.dumps(
            {
                "link_share_entity": "tenant_editable",
                "share_entity": "same_tenant",
                "comment_entity": "anyone_can_edit",
                "security_entity": "anyone_can_edit",
            },
            ensure_ascii=False,
        ),
    ]

    last_output = ""
    for attempt in range(5):
        proc = subprocess.run(cmd, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        last_output = proc.stdout + proc.stderr
        if proc.returncode == 0:
            return True

        if "frequency limit" in last_output or "rate_limit" in last_output:
            time.sleep(8 + attempt * 4)
            continue

        raise RuntimeError(last_output)

    raise RuntimeError(f"rate limit persisted while setting permission for {doc_id}: {last_output}")


def escape_xml(text: str) -> str:
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("spec", help="Path to JSON spec.")
    parser.add_argument(
        "--make-editable",
        action="store_true",
        help="Set generated docx links to tenant-editable.",
    )
    args = parser.parse_args()

    spec = json.loads(Path(args.spec).read_text(encoding="utf-8"))
    results = []
    for doc in spec["docs"]:
        result = create_doc(doc["title"], doc["owner"], doc["xml"])
        if args.make_editable:
            result["editable"] = make_editable(result["doc_id"])
        results.append(result)
        time.sleep(4)

    print(json.dumps(results, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
