---
name: qbit-lark-edit
description: Edit Qbit Feishu/Lark draft documents from unresolved sidebar comments while preserving human review visibility. Use when the user asks Codex to apply teacher, editor, client, or collaborator feedback in a Feishu doc, especially small copy edits, insertions, deletions, paragraph breaks, Markdown-friendly formatting, or review-pass changes that must keep comments alive. Always mark additions and rewrites with yellow highlight, represent deletions with strikethrough instead of removing source text, and do not resolve comments unless explicitly requested.
---

# Qbit Lark Edit

## Core Rules

Treat Feishu document comments as review instructions, then make the smallest visible edit that satisfies the comment.

- Keep unresolved comments unresolved unless the user explicitly asks to resolve them.
- Read the comment, replies, and surrounding document context before editing.
- Preserve the original commented text when possible so the sidebar comment remains attached.
- Mark every added or rewritten phrase with yellow highlight.
- Represent requested deletions with strikethrough on the original text.
- Use an extra blank line when an edit creates paragraph breaks or Markdown-style line separation.
- Avoid broad rewrites when the comment only asks for a local fix.

Preferred inline markup:

```markdown
<text background-color="yellow">new or changed text</text>
~~text requested for deletion~~
```

## Workflow

1. Get unresolved comments for the document.

```bash
lark-cli drive file.comments list --params '{"file_token":"<DOCX_TOKEN>","file_type":"docx","is_solved":false}'
```

2. Read full reply threads when comments have replies or truncated context.

```bash
lark-cli drive file.comment.replys list --params '{"file_token":"<DOCX_TOKEN>","comment_id":"<COMMENT_ID>","file_type":"docx"}'
```

3. Fetch the relevant document area with block IDs.

```bash
lark-cli docs +fetch --api-version v2 --doc "<DOC_URL_OR_TOKEN>" --detail with-ids
```

For long drafts, narrow the fetch with keyword, section, or range scope after locating the comment target.

4. Apply one local edit per comment target.

Use `docs +update` with the installed CLI's supported flags. Prefer `str_replace` around the smallest stable text span.

```bash
lark-cli docs +update --api-version v2 \
  --doc "<DOC_URL_OR_TOKEN>" \
  --command str_replace \
  --pattern "old local text" \
  --content "old local text <text background-color=\"yellow\">new addition</text>" \
  --doc-format markdown
```

5. Verify the edited area.

- Yellow highlight wraps every insertion and rewrite.
- Strikethrough keeps deletion targets visible.
- Extra blank lines appear where paragraph separation was requested.
- Comments remain unresolved.
- Unrelated blocks and Feishu resource tags remain unchanged.

## Edit Patterns

### Add Text

Before:

```markdown
OpenAI 发布了新模型。
```

After:

```markdown
OpenAI 发布了新模型，<text background-color="yellow">主打更强的长文本理解和工具调用能力</text>。
```

### Delete Text

Before:

```markdown
这项技术已经彻底解决了行业全部问题。
```

After:

```markdown
这项技术已经~~彻底解决了行业全部问题~~。
```

### Rewrite Text

Before:

```markdown
这家公司突然火了。
```

After:

```markdown
~~这家公司突然火了。~~<text background-color="yellow">这家公司在新一轮产品发布后重新进入行业视野。</text>
```

### Split Paragraphs

Before:

```markdown
第一层是模型能力。第二层是应用落地。
```

After:

```markdown
第一层是模型能力。

<text background-color="yellow">第二层是应用落地。</text>
```

### Mixed Local Edit

Before:

```markdown
这个结果说明所有公司都会马上采用该方案。
```

After:

```markdown
这个结果说明~~所有公司都会马上采用该方案~~<text background-color="yellow">头部公司正在加速评估该方案</text>。
```

## Guardrails

- Do not use whole-document overwrite for comment cleanup.
- Do not remove the source text of a commented passage just to make the final prose cleaner.
- Do not resolve, delete, hide, or archive comments during the edit pass.
- Do not rely on comment snippets alone; inspect the document context around the anchor.
- Preserve Feishu resource tags exactly, including `<img>`, `<sheet>`, `<bitable>`, `<whiteboard>`, `<cite>`, and `<synced_reference>`.
- If a comment asks for creative expansion beyond a small edit, make a conservative highlighted proposal and leave the final judgment to the user.
