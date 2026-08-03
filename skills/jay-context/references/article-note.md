# Article-Note

## Purpose

Use this reference when the user provides article text, article links, transcript Markdown, polished transcript Markdown, or first-hand source material and wants an Obsidian-ready note section.

The goal is to turn the source into a clear structured summary in the resolved `output_language`, then place it as the first section of the same Markdown document that contains the converted source article or transcript. Focus on faithful language conversion,information compression,hierarchy rebuilding,and concise presentation. Do not force subjective judgment,commentary,elevation,or second-hand creation. Remove intro storytelling,screenshots,proof-of-reading chatter,token-count anecdotes,platform-specific detours,and other low-value material from the note section unless a case is required to understand the source content.

This reference also owns the single `Final Filename Contract` for every Jay-Context source type. Article,interview,audio,video,event,and batch routes point here instead of maintaining naming rules locally.

## Contents

- Inputs and delivery shape
- Entry routes and note writing
- Link,text,and transcript SOPs
- Global path routing
- Final Filename Contract
- Delivery check

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

Deliver note-entry work as one merged Markdown document. The extracted note is the first content section at the top of the document,followed by the `output_language` article,existing transcript,converted transcript,or polished transcript content.

Default shape:

```markdown
# <document title>

## <localized notes label>

### <source-appropriate heading>

- <compressed point from the source>
- <compressed point from the source>

### <source-appropriate heading>

#### <optional layer or dimension>

- <compressed point from the source>
- <compressed point from the source>

#### <optional layer or dimension>

- <compressed point from the source>
- <compressed point from the source>

## <localized source-text label>

<output_language article,converted transcript,or polished transcript content>

*<localized source label>: <source URL>*
```

When the source document already starts with `# <title>`,translate the semantic title when needed and insert the localized notes heading directly below it. When the source document has no title,add a concise `output_language` title first. Do not create a standalone note file,raw/source archive,or article-title folder unless the user explicitly asks for that package.
For URL-based sources,append one italicized body line using the localized source label and exact original input URL at the end of the document. Do not add a dedicated source heading or replace the URL with link text. Preserve query parameters and fragments. For pasted prose or local files without a source URL,omit this line unless the user supplies a canonical URL.

## Entry Routes

Use these routes before writing:

- Complete article route: for WeChat links,article URLs,pasted full articles,and Markdown articles,fetch or read the complete article,translate it faithfully when needed,keep only the `output_language` body,and insert the localized notes section at the top. Do not editorially polish the translated article.
- Existing transcript route: when the user selects or supplies a transcript Markdown file and asks for notes,edit that file in place unless the user gives another destination. Convert its semantic content when needed and insert the localized notes section above the transcript body.
- Polished transcript plus note route: use this only after the current source owner has produced polished transcript Markdown. The input is exactly one polished Markdown path. Treat that file as the complete and polished source. Insert or replace the localized notes section at the top of that same file,preserve the polished transcript body below it,then continue with the same source owner. Do not fetch media,run or poll ASR,read temporary source-language transcript files,polish transcript prose,create a new archive package,or split the source into separate files.
- Direct first-hand note route: when the user provides first-hand source material and asks directly for notes,obtain and convert the article or transcript,create one Markdown document with the localized notes section first and converted source material below it,and skip transcript polishing.

## Note Section Shape

Use the delivery-language contract's localized notes label as the default section heading unless the user asks for another heading. Inside it,organize the source with flexible localized `###` and optional `####` headings that fit the material itself.

## Writing Rules

- Summarize and reorganize the source content into clearer hierarchy, shorter expression, and reusable reading notes.
- Preserve the source's main topics, facts, numbers, chronology, categories, methods, examples, and relationships when they are important.
- Remove story intros, personal setup, screenshots, image captions, defensive caveats, repeated examples, and long source-specific chronology when they do not carry information.
- Keep examples only when they make the source content easier to understand or reuse.
- Do not summarize paragraph by paragraph.
- Do not force subjective judgment, value ranking, commentary, reflection, or extrapolated implications.
- Do not produce a media article rewrite.
- Translate source content faithfully into `output_language` when needed. Do not add editorial rewriting in the article,existing transcript,or direct first-hand note route unless the user explicitly asks for source cleanup.
- Do not add invented facts, extra citations, or outside claims unless the user asks for research.
- Keep the writing dense, clean, and suitable for later retrieval in Obsidian.
- Prefer short sections and bullets where the idea is naturally list-shaped.
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
2. Identify the source's main topics, information hierarchy, important facts, categories, process, and examples.
3. Remove anecdotal setup unless it carries important information.
4. Convert the source content into the Note Section Shape and insert it at the top of the same Markdown document.
5. Choose the final filename only through the `Final Filename Contract`.

## Existing Markdown SOP

1. Read the current Markdown file.
2. If a top-level title exists, keep it as the first line.
3. Insert or replace the localized notes section immediately after the title and before the existing body.
4. Convert the existing source body to `output_language` when needed and keep only that version below the note section.
5. If a previous localized notes section exists and the user wants an update,replace that section instead of appending a duplicate.

## Polished Transcript SOP

Use this SOP when the caller says the Markdown is already polished:

1. Read only the provided polished Markdown file and this reference.
2. Confirm the file has polished transcript prose below the title. If it starts with a top-level title, keep that title as the first line.
3. Build the note from the polished transcript body, focusing on structured summary, information compression, and clear hierarchy.
4. Insert or replace the localized notes section immediately below the title.
5. Preserve the full polished transcript below the note section, including existing speaker labels and headings.
6. Edit the same Markdown path in place unless the caller provides a separate final output path.
7. Reply to the caller with the completed Markdown path only.

## Global Path Routing

After a new merged note document is drafted, route it using the parent skill's Global Obsidian Path Router. When the user selected an existing Markdown file, edit that file in place unless the user requests another path.

Default folders:

- `FUTURE`:科技、AI、商业、公司、产品、管理、职业、媒体、创作者经济、工作相关知识。
- `LIFE`:生活、关系、健康、家庭、旅行、居住、消费、个人经验、日常反思。

Choose the folder by the note's primary future use. When the note can fit both, choose `FUTURE` if it will mainly support work, writing, research, technology, or business judgment.

## Final Filename Contract

Use this contract for every new final Markdown filename produced by Jay-Context,including articles,newsletters,interviews,podcasts,videos,audio,event transcripts,paper explanations,reposts,and existing transcripts. Other route references must point here instead of restating naming rules.

### Default Shape

```text
<first-hand-source>-<primary-topic>-<YYYYMMDD>.md
```

For a WeChat source whose page-script date cannot be found,use:

```text
<first-hand-source>-<primary-topic>-未知.md
```

A user-specified filename or absolute output path takes priority.

Before naming,resolve and retain these workflow fields:

- `source_date`: `YYYYMMDD`,or `未知` for a WeChat source without a page-script date.
- `date_source`: the metadata field or fallback that supplied `source_date`.

These workflow fields do not need to appear in the final Markdown unless the user requests metadata.

### Compression Principle

- Keep exactly one source field,one primary-topic field,and one date field.
- Preserve the smallest set of fields that keeps the note identifiable and useful.
- Do not concatenate multiple peer topics into the second field.
- Do not copy a long article,podcast,video,paper,or event title into the filename.

### First Field: First-Hand Source

Choose the person or entity closest to the original knowledge,claim,experience,research,product decision,or event content.

Use this priority:

1. Original speaker,interviewee,researcher,paper author,creator,operator,or practitioner whose first-hand material carries the note.
2. Original lab,institution,company,project,or event organizer when no single first-hand person is identifiable or multiple equal speakers form a collective source.
3. Page author,host,uploader,translator,editor,media account,newsletter,or publication only when that party contributes substantive original analysis,judgment,experience,reporting,or framing that becomes the note's primary value.
4. Source site only when no stronger first-hand source can be identified.

For interviews,use the interviewee or original speaker. Keep the host,interviewer,media account,and uploader out of the first field unless their substantive new context dominates the note.

For paper explanations,reposts,translations,video transfers,or transcript transfers,use the original paper author,researcher,speaker,or creator. Do not use the reposter merely because their account published the page.

When the reposter or article author adds substantive original interpretation,critique,experience,reporting,or a new analytical framework,use that author only when the new context is the note's primary value. A short introduction,translation,summary,or connective commentary does not qualify.

When several first-hand people are equally central and no single person dominates,use the original collective entity. Do not stack a long list of names into the first field.

### Second Field: One Primary Topic

Choose the single most first-principles topic that best explains what the note is fundamentally about. The topic may be a product name,technical term,method,system,role,business model,management concept,company mechanism,or another precise concept.

Preserve canonical spelling and casing for product names and technical terms. English and mixed-language topics are allowed.

When the source covers several topics:

1. Identify the topic with the greatest explanatory power for the whole source.
2. Prefer the underlying mechanism or central object over a broad umbrella category.
3. Keep only that topic in the filename.
4. Put secondary topics in the Markdown title,headings,notes,or metadata.

Do not join peer topics with `和`,`与`,`&`,`+`,slashes,commas,or repeated hyphen fields.

Avoid vague second fields such as `问题`,`对话`,`思考`,`讨论`,`内容`,`分享`,`这个`,`事情`,`文章笔记`,or `未命名`.

### Date Field

For WeChat sources:

1. Fetch the raw page HTML when exporter Markdown or JSON does not expose a publication date.
2. Prefer the inline page-script value `var createTime = 'YYYY-MM-DD HH:mm'`.
3. When `createTime` is absent,use `var oriCreateTime = '<unix-seconds>'` or `ori_create_time: '<unix-seconds>'` and convert it in `Asia/Shanghai`.
4. When neither page-script value exists,set `source_date` to `未知` and `date_source` to `unknown`.
5. Never use the task execution date,fetch date,download time,file modification time,or file creation time as a WeChat filename date.

Use these exact WeChat `date_source` values:

- `wechat_page_script.createTime`
- `wechat_page_script.oriCreateTime`
- `unknown`

For other source types,use the source's publication,recording,event,or document date. Prefer the date closest to the original first-hand material. Use the fetch or creation date only when no source date exists. Record a concise `date_source` such as `source_metadata`,`platform_metadata`,`event_metadata`,`document_metadata`,`fetch_time`,or `creation_time`.

Format known dates as `YYYYMMDD`.

### Branch Guidance

- Article or newsletter: first-hand origin of the material,one core topic,publication date.
- WeChat: first-hand origin,one core topic,page-script date or `未知`.
- Interview,podcast,or video: interviewee or original speaker,one core topic,recording or publication date.
- Paper explanation or repost: original paper author or research institution,one core research topic,original paper date when available.
- Event: dominant first-hand speaker when one clearly carries the material;otherwise the original organizer or collective entity,one core event topic,event date.
- Existing transcript: infer the original speaker or source from transcript metadata before using the file owner or platform.

### Final Check

Before delivery,confirm:

- The first field names the strongest available first-hand source.
- A reposter,host,translator,or media account has not displaced the original source without substantive new context.
- The second field contains one primary topic.
- Product and technical names retain their canonical form.
- Ordinary semantic title and topic text uses `output_language`;people,institutions,products,and technical names retain their canonical searchable form.
- The filename date equals `source_date`.
- `date_source` identifies the evidence used.
- A WeChat filename never uses the task execution or file-system date.
- Unsafe filename characters are removed.
- New merged note documents are saved directly under the routed parent folder unless the user specifies another destination.
- Note-entry work remains one merged Markdown document unless the user explicitly requests a folder package.

## Delivery Check

Before reporting completion:

- Confirm the merged Markdown file exists.
- Confirm the file starts with the `output_language` document title,then the localized notes section before converted source content.
- Confirm the note section is a structured, concise summary of the source content, not commentary, reflection, or a narrative recap.
- Confirm the file is under the routed folder unless the user selected an existing file or explicitly requested another path.
- Confirm obvious boilerplate and intro story material have been removed.
- For URL-based sources,confirm the file ends with the localized italicized source line containing the exact original input URL and has no dedicated source heading.
- Confirm no source-language article,transcript,quotation body,or fetched page copy remains after successful conversion.
- Confirm the final filename follows the `Final Filename Contract`,including `source_date` and `date_source`.
