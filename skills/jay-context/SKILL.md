---
name: jay-context
description: Turn one or many articles, web pages, video/audio links, local recordings, platform transcripts, event transcripts, and raw interview texts into usable Markdown context in the resolved output language for writing and Obsidian. Use when the user asks to fetch articles, transcribe podcasts or videos, connect audio/video material to a text workflow, extract notes, polish transcript prose, or process multiple source links in parallel. Keep one source owner responsible for each source from acquisition through final Markdown; use the current main agent for one source and one end-to-end worker per source for batches.
---

# Jay-Context

## Purpose

Turn multimodal sources into text-ready context and routed Markdown in the resolved `output_language`. Keep source acquisition,ASR,language conversion,transcript readiness,polishing,note packaging,and final-path routing as separate stages owned by one agent per source.

Resolve every relative path from this skill directory.

## Resources

- Read `references/article-note.md` for article inputs,existing transcript notes,direct first-hand note requests,and the single final filename contract used by every source type.
- Read `references/wechat-exporter-backend.md` before fetching `mp.weixin.qq.com/s/...`.
- Read `references/audio-to-text.md` for podcast, video, audio, local recording, local media acquisition, Flash preprocessing, segmentation, and raw-transcript output.
- Read `references/interview-polish.md` before polishing transcript prose or packaging final audio Markdown.
- Read `references/event-transcript.md` for salons, panels, workshops, conferences, roadshows, and similar event transcripts.
- Read `references/batch-dispatch.md` when the input contains two or more distinct URLs.
- Run `scripts/transcribe_media.py` for local media acquisition and Doubao ASR routing.
- All audio/video ASR uses Doubao. Platform captions bypass ASR. When Doubao fails,record the attempt state and report the failure.
- Run `scripts/doubao_asr.py` only for direct local-file Doubao Flash submission or diagnostics.

## Working Locations

- Use `~/Downloads/<source-slug>/` for downloaded media,temporary acquisition artifacts,converted transcripts,and content-free processing status unless the user gives another working path.
- Keep intermediate media and converted working transcripts outside the repository.
- Route final Markdown through the Obsidian router unless editing an existing selected Markdown file.
- Expand `${HOME}` at runtime. Default vault root: `${HOME}/Library/Mobile Documents/iCloud~md~obsidian/Documents`.
- Route work,technology,AI,business,commercial,product,company,career,management,media,and professional knowledge to `FUTURE`.
- Route life,relationships,reflection,health,travel,home,family,and everyday experience to `LIFE`.
- A user-specified folder or absolute output path takes priority.

## Output Language Contract

- Resolve `output_language` from the active Myoo delivery-language contract. Default to `zh-CN` when the field is absent or invalid.
- A language explicitly requested by the user for the current task overrides the stored preference for that task only.
- Apply `output_language` to replies,document titles,headings,notes,article bodies,captions,transcripts,quotations,generic speaker labels,source labels,and final Markdown.
- Preserve official or standard searchable forms for people,companies,products,technical terms,code,identifiers,numbers,and URLs.
- When acquired semantic content uses another language,translate it faithfully into `output_language` before polishing,summarizing,or final packaging.
- Keep only the `output_language` version after successful conversion. Source-language article text,captions,transcripts,and ASR response bodies are temporary and must be removed after the translated working text passes validation.
- Do not rewrite historical Markdown when the setting changes. Existing files are converted only when the user explicitly submits them for processing.
- Use the localized structure labels supplied by the active delivery-language contract instead of hard-coded Chinese headings.
- When no label table is supplied,translate the semantic labels for title,notes,body,source text,source,and follow-up questions naturally into `output_language`. For the default `zh-CN`,use `标题`,`笔记`,`正文`,`原文`,`来源`,and `跟踪方向`.

## Source Ownership

- Normalize surrounding whitespace and deduplicate only exact duplicate URLs. Preserve query parameters and source order.
- One distinct URL or one local source: the current main agent is the source owner and completes the full workflow without spawning a subagent.
- Two or more distinct URLs: the current main agent becomes the batch coordinator. Read `references/batch-dispatch.md`,then assign one end-to-end worker per source.
- A source owner never calls `spawn_agent` and never creates a separate acquisition,ASR,polishing,note,or validation agent.
- `interview-polish`,`article-note`,and `event-transcript` are execution rules for the current source owner. They are not agent handoff points.

## Source Router

1. Identify the source.
   - Article: pasted prose,Markdown,newsletter,WeChat,Weibo,Feishu Docx/wiki,or ordinary web page.
   - Audio/video: podcast page,RSS episode,direct media URL,YouTube,Bilibili,local recording,or local video.
   - Existing transcript: timestamps,speaker labels,platform transcript,caption file,or rough dialogue.
   - Event transcript: prepared talk,roundtable,audience Q&A,venue chatter,or follow-up conversation.
2. Choose the shortest faithful bridge to text.
   - Complete article text: use the article branch.
   - Existing verbatim transcript or usable platform captions: convert them to `output_language`,persist only the converted working transcript,and skip ASR.
   - YouTube URL: always run `scripts/transcribe_media.py`. It must first use `yt-dlp --cookies-from-browser chrome` to look up and download one usable manual or automatic caption track. Convert the caption to `output_language`,persist only the converted transcript and content-free status,and skip ASR when that succeeds.
   - Bilibili URL: always run `scripts/transcribe_media.py`. It must first use `yt-dlp --cookies-from-browser chrome --skip-download --write-subs --sub-langs ai-zh --sub-format srt` to download the Chinese AI caption track. Convert the caption to `output_language`,persist only the converted transcript and content-free status,and skip ASR when that succeeds. Do not rely on `--dump-single-json` to discover Bilibili captions because the authenticated extractor may list `ai-zh` while returning an empty subtitle map in dumped metadata.
   - YouTube or Bilibili caption failure: download local audio and use Doubao Flash as the fallback.
   - Every other audio/video URL: use the local-audio route directly.
   - Platform audio/video without usable source text: download the media locally with `yt-dlp`,then submit the local audio to Doubao Flash. On Doubao failure,report the failure.
   - Direct public media URL: download the media locally,then submit the local file to Doubao Flash. Never send the public URL to Doubao.
   - Downloaded platform media: submit the local file to Doubao Flash with Base64. On Doubao failure,report the failure.
   - Local media: submit the local file to Doubao Flash with Base64. On Doubao failure,report the failure.
3. Choose the text downstream.
   - Ordinary podcast/video/audio delivery: the source owner creates an `output_language` working transcript,reads `references/interview-polish.md`,then produces the localized notes section plus the polished body in one Markdown file.
   - Direct note request: the source owner applies `references/article-note.md` to the converted transcript or article and skips prose polishing unless requested.
   - Event material: the source owner follows `references/event-transcript.md`.
   - Existing selected Markdown: edit in place unless the user requests a copy.

## End-to-End Gate

- Treat Doubao ASR output,platform captions,and page transcripts as temporary source-language inputs.
- Detect the source language and convert semantic content to `output_language` before persistent downstream text is created. Skip conversion when the source already matches.
- Save the converted working transcript to disk before any polishing or note generation,validate that it contains no unexplained source-language body,and then remove temporary source-language captions,transcripts,and ASR response bodies.
- Converted transcript readiness is a stage gate inside the same source-owner workflow. It does not trigger a new agent.
- After the converted transcript exists,the same source owner reads the relevant polishing or note reference and continues to final Markdown.
- For ordinary polished delivery,the source owner polishes the converted transcript and packages the localized notes section in the same file.
- For a direct first-hand note request,the source owner applies `references/article-note.md` to the converted transcript without transcript polishing.
- Do not pass large transcript bodies between agents when file paths are available.

## Article and Transcript Branches

- Article-to-note: preserve the complete article meaning in `output_language` and prepend the localized note section in the same Markdown file. Follow `references/article-note.md`.
- Existing-transcript-to-note: convert the transcript when needed,prepend the localized note section,and keep only the converted transcript below it.
- Interview transcript: the source owner applies `interview-polish` before final note packaging.
- Feishu Docx/wiki remains a valid text source. Fetch it as text with the relevant Lark document workflow; do not involve Feishu Minutes.
- Weibo note requests use the verified `weibo.cn/comment/<mblogid>` route documented in the existing article branch.

## Local Markdown Cleanup

Before writing final or source-preserving Markdown:

- Trim trailing spaces and tabs outside fenced code blocks.
- Collapse three or more consecutive blank lines to one blank line.
- Preserve content order,headings,lists,blockquotes,links,tables,images,escaped characters,and source meaning during language conversion.
- Skip cleanup when the user requests spacing-exact or byte-exact preservation.

## Source Owner Contract

- Finish acquisition,ASR,language conversion,temporary-source cleanup,polishing,note packaging,filename selection,routing,and self-check inside the same agent.
- Before choosing or changing any final Markdown filename,apply the `Final Filename Contract` in `references/article-note.md`.
- For audio/video polished delivery,read the full `references/interview-polish.md` only after the converted transcript exists.
- For event material,read both `references/interview-polish.md` and `references/event-transcript.md`.
- Produce one final Markdown file per source unless the user explicitly requests a combined synthesis.
- For every URL-based source,append a final italicized body line using the localized source label and the exact original input URL. Do not add a dedicated source heading. Preserve query parameters and fragments.
- In batch mode,return the structured worker result defined in `references/batch-dispatch.md`.

## Delivery Checks

- Confirm every expected final Markdown file exists.
- For note outputs,confirm the localized notes heading appears before the source or polished body.
- For successful YouTube or Bilibili caption runs,confirm the converted transcript and content-free processing status exist,`doubao_attempted` is false,and source-language caption artifacts have been removed after validation.
- For ASR runs,confirm the converted transcript and content-free processing status exist and the source-language response body has been removed after validation.
- For platform-page ASR runs,confirm the expected media and content-free acquisition metadata exist in the working directory.
- Confirm media at or above 20MiB was normalized to 16kHz mono 64kbps MP3 before Flash submission.
- Confirm media longer than 2 hours was split into non-overlapping 110-minute segments,merged in source order,and had temporary prepared files removed after complete success.
- Confirm the final filename uses the strongest first-hand source and exactly one primary topic.
- Confirm the final filename date matches the resolved `source_date` and its recorded `date_source` under the `Final Filename Contract`.
- For URL-based sources,confirm the final Markdown ends with the localized italicized source line containing the exact original input URL and has no dedicated source heading.
- Confirm no source-language article body,caption,transcript,quotation page,or ASR response body remains after successful conversion.
- The source owner validates its own Markdown structure and content.
- In batch mode,the coordinator verifies worker-created Markdown by file existence only unless the user asks for review or debugging.
- Report the source URL or request ID,local media path,Doubao attempt state,converted transcript path,processing-status path,and final Markdown path.

## Hard Boundaries

- Do not route audio through Feishu Drive or Feishu Minutes.
- Do not treat ASR JSON,platform captions,or unconverted transcript text as polished final Markdown.
- Do not generate article-style notes before transcript readiness when polished transcript prose is requested.
- Do not create a second note file for audio output; package notes and polished body together.
- Do not expose the Doubao API key in commands,logs,Markdown,or subagent prompts.
- Do not submit temporary signed stream URLs resolved by `yt-dlp` to Doubao.
- Use Doubao Flash with local Base64 media only. Do not use the standard async API,public media URLs,submit/query polling,or another ASR engine.
- When Doubao fails,record the Doubao attempt state and primary failure,and report the failure instead of falling back to a local engine.
- When language conversion fails,do not create a partial final Markdown file. Remove temporary source-language content,retain only a content-free failure state,and report the primary failure.
- Do not split one source across acquisition,ASR,polishing,note,or validation agents.
- Only the batch coordinator may spawn source workers. A source worker must not spawn or delegate to another agent.
