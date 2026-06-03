---
name: feishu-doc-edit
description: Review and revise Feishu/Lark documents from sidebar comments while preserving visible change marks. Use when the user asks Codex to process Feishu document comments, resolve sidebar feedback, edit a Feishu doc in review mode, or make additions/deletions/rewrites without silently changing the original text. Requires new or changed text to be highlighted yellow and deletions to be represented with strikethrough instead of direct removal.
---

# Feishu Doc Edit

## Core Rule

When applying Feishu document sidebar comments, never silently overwrite the document.

- Additions: insert new text as yellow-highlighted text.
- Rewrites: keep the replacement visible as yellow-highlighted text.
- Deletions: keep the original text and apply strikethrough.
- Mixed edits: use strikethrough for removed wording and yellow highlight for inserted wording.

Preferred inline markup:

```markdown
<text background-color="yellow">new or changed text</text>
~~text that should be deleted~~
```

## Workflow

1. Read current unresolved sidebar comments first.

```bash
lark-cli drive file.comments list --params '{"file_token":"<DOCX_TOKEN>","file_type":"docx","is_solved":false}'
```

2. If any comment has `has_more=true`, fetch all replies before deciding what to change.

```bash
lark-cli drive file.comment.replys list --params '{"file_token":"<DOCX_TOKEN>","comment_id":"<COMMENT_ID>","file_type":"docx"}'
```

3. Fetch the affected document section with block IDs.

```bash
lark-cli docs +fetch --api-version v2 --doc "<DOC_URL_OR_TOKEN>" --detail with-ids
```

For large documents, prefer `--scope keyword`, `--scope section`, or `--scope range` once the relevant area is known.

4. Apply the smallest possible update using `docs +update`.

Use the installed CLI's supported flags. Current common form:

```bash
lark-cli docs +update --api-version v2 \
  --doc "<DOC_URL_OR_TOKEN>" \
  --command str_replace \
  --pattern "old local text" \
  --content "old local text <text background-color=\"yellow\">new addition</text>" \
  --doc-format markdown
```

For block-level replacement, preserve all unrelated content and only replace the target block.

5. Verify after editing.

Fetch the changed area and check:

- Yellow highlight exists around every added or changed phrase.
- Deleted text is still present with `~~...~~`.
- No unrelated blocks changed.
- The comment intent was addressed.

## Edit Patterns

### Add Text

Before:

```markdown
Codex can operate local files.
```

After:

```markdown
Codex can operate local files，<text background-color="yellow">也可以结合终端、插件和 Skill 串起完整工作流</text>。
```

### Delete Text

Before:

```markdown
这个能力完全没有风险。
```

After:

```markdown
这个能力~~完全没有风险~~。
```

### Rewrite Text

Before:

```markdown
Codex 是一个聊天工具。
```

After:

```markdown
~~Codex 是一个聊天工具。~~<text background-color="yellow">Codex 更像一个能读写本地文件、调用终端和连接外部工具的桌面 agent。</text>
```

### Partial Rewrite

Before:

```markdown
建议直接打开完全访问权限。
```

After:

```markdown
建议~~直接打开完全访问权限~~<text background-color="yellow">先使用自动审查权限，熟悉后再按任务需要提高权限</text>。
```

## Guardrails

- Do not use `overwrite` for a whole document unless the user explicitly asks for a full rebuild and accepts loss of review visibility.
- Do not delete text blocks to satisfy deletion comments; strikethrough the exact text instead.
- Do not mark comments resolved unless the user explicitly asks.
- Do not rely only on comment snippets. Read the surrounding document context before changing text.
- Preserve Feishu resource tags such as `<img>`, `<sheet>`, `<bitable>`, `<whiteboard>`, `<cite>`, and `<synced_reference>` exactly when they appear in fetched content.
- If a requested edit would make the document confusing with visible review marks, add a short yellow-highlighted bridging phrase rather than cleaning the original invisibly.
