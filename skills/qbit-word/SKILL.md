---
name: qbit-word
description: "Qbit document conversion router for Feishu/Lark and Word workflows. Use when the user asks to export a confirmed Feishu/Lark outline to the Qbit Word template, convert/download a Feishu document as Word, rename a Word output from a Feishu title, save Qbit .docx files to Downloads, or import a local Markdown draft into a real Feishu docx document while preserving Qbit article line breaks and rendering Markdown-linked images/videos as real media blocks."
---

# Qbit Word Router

This skill only routes to the matching subskill. Read exactly one subskill unless the user asks for a combined workflow.

## Route

- **Local Markdown draft → Feishu docx**: read `subskills/feishu-markdown-import.md`.
  Use when the user gives a local `.md` draft and asks to import it into Feishu/Lark, keep Markdown-style spacing, keep Qbit draft text unchanged, or turn image/video links and Obsidian embeds into real Feishu media blocks.
- **Feishu/Lark outline → Qbit Word**: read `subskills/feishu-outline-word.md`.
  Use when the user gives a Feishu/Lark wiki/docx URL and asks to export, download, paste into the Qbit Word template, save as `.docx`, or use the local Qbit outline template.

## Router Rules

- Do not run the old Word export script from this file directly. Delegate to `subskills/feishu-outline-word.md`.
- Do not recreate the Markdown import procedure ad hoc. Delegate to `subskills/feishu-markdown-import.md`.
- If the user request includes both importing Markdown to Feishu and exporting that Feishu document to Word, run the Markdown import subskill first, then run the Word export subskill on the resulting Feishu URL.
- Keep live Feishu edits conservative: preserve original wording, links, media order, and Qbit draft structure unless the user explicitly asks for rewriting.
