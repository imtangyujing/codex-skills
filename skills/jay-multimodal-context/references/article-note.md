# Article-Note

## Purpose

Use this reference when the user provides article text, article links, transcript Markdown, polished transcript Markdown, or first-hand source material and wants an Obsidian-ready note section.

The goal is to extract transferable views, frameworks, judgments, and useful concepts, then place them as the first section of the same Markdown document that contains the source article or transcript. Remove intro storytelling, screenshots, proof-of-reading chatter, token-count anecdotes, platform-specific detours, and other case material from the note section unless a case is required to understand the argument.

## Inputs

Accepted inputs:

- Pasted article text
- Markdown article text
- Article URL
- Newsletter URL
- Web page URL
- Local text or Markdown file containing an article
- Local Markdown file containing a transcript
- Polished transcript Markdown produced by the parent workflow
- Raw first-hand transcript material when the user asks directly for notes

For links, fetch the source content before writing the note. If the page is inaccessible, use any content the user supplied in the chat and clearly mention the access issue in the working update.

## Delivery Shape

Deliver note-entry work as one merged Markdown document. The extracted note is the first content section at the top of the document, followed by the original article, existing transcript, raw transcript, or polished transcript content.

Default shape:

```markdown
# <document title>

## 笔记

### 核心观点

<1-3 paragraphs stating the central thesis.>

### 关键判断

- <important judgment>
- <important judgment>
- <important judgment>

### 分层框架

#### <framework layer or dimension>

<compressed explanation>

#### <framework layer or dimension>

<compressed explanation>

### 金句

> 原文摘句。

> 原文摘句。

> 原文摘句。

### 延伸思考

- <question or implication worth keeping>
- <question or implication worth keeping>

## 原文

<source article, existing transcript, raw transcript, or polished transcript content>
```

When the source document already starts with `# <title>`, keep that title and insert `## 笔记` directly below it. When the source document has no title, add a concise title first. Do not create a standalone note file, raw/source archive, or article-title folder unless the user explicitly asks for that package.

## Entry Routes

Use these routes before writing:

- Complete article route: for WeChat links, article URLs, pasted full articles, and Markdown articles, fetch or read the complete article, preserve its body, and insert `## 笔记` at the top. Do not polish the article.
- Existing transcript route: when the user selects or supplies a transcript Markdown file and asks for notes, edit that file in place unless the user gives another destination. Insert `## 笔记` above the transcript body.
- Polished transcript plus note route: use this only after polished transcript Markdown already exists. The caller may be the same polishing subagent that just produced the Markdown. The input is exactly one polished Markdown path. Treat that file as the complete and polished source. Insert or replace `## 笔记` at the top of that same file, preserve the polished transcript body below it, then return the completed Markdown path to the caller. Do not fetch media, create or poll Feishu Minutes, read raw transcript files, polish transcript prose, create a new archive package, or split the source into separate files.
- Direct first-hand note route: when the user provides first-hand source material and asks directly for notes, obtain the article or raw transcript, create one Markdown document with `## 笔记` first and source material below it, and skip transcript polishing.

## Note Section Shape

Use `## 笔记` as the default section heading unless the user asks for another heading. Inside it, use these subsections when the material supports them: `### 核心观点`, `### 关键判断`, `### 分层框架`, `### 金句`, and `### 延伸思考`. Omit empty subsections.

## Writing Rules

- Extract the source's观点,框架,判断,方法,推论.
- Remove story intros, personal setup, screenshots, image captions, defensive caveats, repeated examples, and long source-specific chronology.
- Keep examples only when they make an abstract idea easier to reuse.
- Do not summarize paragraph by paragraph.
- Do not produce a media article rewrite.
- Do not polish or rewrite source content in the article route, existing transcript route, or direct first-hand note route. Only add the note section unless the user explicitly asks for source cleanup.
- Do not add invented facts, extra citations, or outside claims unless the user asks for research.
- Keep the writing dense, clean, and suitable for later retrieval in Obsidian.
- Prefer short sections and bullets where the idea is naturally list-shaped.
- In `## 金句`,use standalone Markdown blockquotes. Keep only short source excerpts that are worth reusing; do not wrap them in list bullets,commentary,or paraphrase.
- Preserve useful terms such asPrompt Engineering,Harness Engineering,Agent,SOP,AI when they are core concepts.
- Follow any standing user style constraints in the active thread, including forbidden sentence patterns and spacing rules.

## Link Handling SOP

1. Open or fetch the link.
2. Extract title, author/source if available, publication date if available, and main body.
3. Ignore nav, comments, ads, related links, social widgets, and newsletter boilerplate.
4. If the link contains embedded media but the article body is enough, process the article body only.
5. If the article depends on audio/video/transcript content, return to the parent multimodal workflow and use the suitable audio/transcript branch.

## Text Handling SOP

1. Treat the pasted text as the source of truth.
2. Identify the thesis, supporting judgments, and reusable framework.
3. Remove anecdotal setup unless it carries a reusable insight.
4. Convert the reusable ideas into the Note Section Shape and insert them at the top of the same Markdown document.
5. Choose a concise filename that names the article or its core idea.

## Existing Markdown SOP

1. Read the current Markdown file.
2. If a top-level title exists, keep it as the first line.
3. Insert or replace a `## 笔记` section immediately after the title and before the existing body.
4. Preserve the existing source body below the note section.
5. If a previous `## 笔记` section exists and the user wants an update, replace that section instead of appending a duplicate.

## Polished Transcript SOP

Use this SOP when the caller says the Markdown is already polished:

1. Read only the provided polished Markdown file and this reference.
2. Confirm the file has polished transcript prose below the title. If it starts with a top-level title, keep that title as the first line.
3. Build the note from the polished transcript body, focusing on reusable观点,框架,判断,方法,推论.
4. Insert or replace `## 笔记` immediately below the title.
5. Preserve the full polished transcript below the note section, including existing speaker labels and headings.
6. Edit the same Markdown path in place unless the caller provides a separate final output path.
7. Reply to the caller with the completed Markdown path only.

## Global Path Routing

After a new merged note document is drafted, route it using the parent skill's Global Obsidian Path Router. When the user selected an existing Markdown file, edit that file in place unless the user requests another path.

Default folders:

- `FUTURE`:科技、AI、商业、公司、产品、管理、职业、媒体、创作者经济、工作相关知识。
- `LIFE`:生活、关系、健康、家庭、旅行、居住、消费、个人经验、日常反思。

Choose the folder by the note's primary future use. When the note can fit both, choose `FUTURE` if it will mainly support work, writing, research, technology, or business judgment.

## Filename Rules

- Default pattern for article and note-entry files: `<author-or-source>-<original-title>-<YYYYMMDD>.md`.
- Use the article author as the first field. If the author is unavailable, use the media account, newsletter name, publication, company, or source site.
- Use the original title as the second field. If the title is vague or missing, write a short Chinese title that captures the core idea.
- Use the publication date as the date field. If publication date is unavailable, use the fetch or creation date.
- Keep note-entry work as one merged Markdown document. Do not create a folder package unless the user explicitly asks for one.
- Remove characters that are unsafe or awkward in filenames.
- Save new merged note documents directly under the routed parent folder.
- Avoid generic filenames such as`文章笔记`,`未命名`,or`note`.

## Delivery Check

Before reporting completion:

- Confirm the merged Markdown file exists.
- Confirm the file starts with the document title, then the `## 笔记` section before source content.
- Confirm the note section contains the core idea, not a narrative recap.
- Confirm the file is under the routed folder unless the user selected an existing file or explicitly requested another path.
- Confirm obvious boilerplate and intro story material have been removed.
