---
name: jay-multimodal-context
description: Convert multimodal source material into usable writing context, especially articles, internet video/audio links, local recordings, Feishu Minutes transcripts, event transcripts, or raw Chinese interview transcripts that need polished interview-style Markdown or Obsidian notes. Use when the user provides article text, article links, Bilibili/video/podcast/audio links, local audio/video files, Feishu Minutes material, or raw transcript text and asks for note extraction, transcription, or interview polishing. This skill coordinates article-note routing, low-bitrate source audio retrieval, Feishu Minutes transcription, event transcript handling, and interview-polish editing while keeping orchestration, transcription, polishing, and final path routing responsibilities separate.
---

# Jay-Multimodal-Context

## Purpose

Use this skill to turn source material into usable Markdown context for writing and Obsidian. The main agent orchestrates source handling, transcript readiness, subagent assignment, file routing, and delivery checks. It does not rewrite interview content when subagents are available.

Resolve all relative paths from the directory containing this `SKILL.md`.

## Bundled Resources

- `references/article-note.md`: read before adding an Obsidian note section to article text, article links, existing transcript Markdown, or non-podcast transcript-derived Markdown.
- `references/wechat-exporter-backend.md`: read before fetching `mp.weixin.qq.com/s/...` article links; use the local exporter path before trying browser-based access.
- `references/interview-polish.md`: read before polishing transcript prose, assigning polishing work, adding final Markdown packaging, or deciding final interview-style Markdown filenames.
- `references/audio-to-minutes.md`: read for internet video/audio, podcast pages, direct MP3 links, local recordings, Feishu Drive upload, Feishu Minutes creation, transcript polling, and low-bitrate audio selection.
- `references/event-transcript.md`: read when a transcript comes from a salon, meetup, panel, workshop, conference, roadshow, or similar event.
- `scripts/podcast_to_minutes.py`: use for podcast pages and direct MP3 links; it downloads the audio, uploads it to Feishu Drive, creates a Minutes record, and prints JSON.

## Working Locations

- Use `~/Downloads` as the working root unless the user explicitly asks for another folder.
- Create source-specific subfolders under `~/Downloads` when raw audio, raw transcripts, and final Markdown need separation.
- Do not create or reuse a `multimodal-context` folder in the current repository or workspace unless the user explicitly requests that path.
- Save raw transcripts under a temporary or source-specific working folder before polishing.
- Route every final Markdown output through the Global Obsidian Path Router unless the user gives an explicit absolute output path.
- For podcast, video, and audio final Markdown, follow `references/interview-polish.md` final packaging and filename rules.

## Local Markdown Persistence Cleanup

Apply this mechanical cleanup immediately before writing any final or source-preserving local `.md` file created by this skill, including fetched Feishu Docx Markdown, article Markdown, transcript-derived Markdown, and routed Obsidian Markdown.

Cleanup rules:

- Trim trailing spaces and tabs on normal text lines.
- Collapse any run of 3 or more blank lines into exactly one blank line.
- Preserve content order, headings, lists, blockquotes, links, tables, image Markdown, escaped Markdown characters, and source wording.
- Do not merge adjacent non-empty lines, rewrite prose, summarize content, or remove media/source links.
- Do not apply this cleanup inside fenced code blocks.
- Skip this cleanup when the user explicitly asks for byte-for-byte or spacing-exact preservation.
- Do not use the cleaned local Markdown as a matching source for Feishu `docs +update` or other exact remote edit operations. Keep the raw fetched content for exact matching workflows.

## Global Obsidian Path Router

Run this step for every final Markdown output. For note tasks, route the merged Markdown document through this step unless editing an existing user-selected Markdown file in place.

Default vault root: `/Users/jay/Library/Mobile Documents/iCloud~md~obsidian/Documents`.

Default folders:

- Technology,AI,business,commercial,product,company,work,career,management,media,creator economy,or professional knowledge goes to `FUTURE`.
- Life,relationships,personal reflection,health,travel,home,family,consumer choices,or everyday experience goes to `LIFE`.

Routing rules:

- Decide the folder from the source topic and the note's primary use.
- If both folders could fit, choose `FUTURE` when the note is mainly useful for work, writing, research, technology, or business judgment.
- If the user explicitly names a folder, use that folder.
- If the user gives another absolute output path, write there and also apply this router when the task is meant to create an Obsidian note.
- Use this router to choose the destination folder. Let the active branch reference decide the final filename.
- Ensure the target folder exists before writing.

## Workflow

1. Identify the input type.
   - Article inputs: raw article text, Markdown, pasted longform prose, article URLs, newsletter URLs, and web pages the user wants turned into notes.
   - Video/audio inputs: Bilibili, podcast pages, RSS episodes, direct MP3/M4A files, local recordings, and similar sources.
   - Raw transcript inputs: timestamped text, speaker-labeled text, Feishu Minutes text, or files containing rough interview dialogue.
   - Event transcript inputs: venue chatter, host introductions, prepared talks, roundtables, audience Q&A, side conversations, or post-event follow-ups from events.
   - Note requests: any request whose desired output is an Obsidian note, reading note, refined note, or context note.
2. Select the branch.
   - Article-to-note branch: read `references/article-note.md`. Use this when the user provides a complete article or article-like source, including WeChat links, Markdown files, pasted longform prose, newsletter URLs, or web pages. Fetch or read the complete article, preserve the article body as source content, and prepend the note section at the top of the same Markdown document. Use `references/article-note.md` filename rules for new files. Do not polish, rewrite, summarize as a standalone note, or split the article into a separate source file unless the user explicitly asks.
   - Existing-transcript-to-note branch: read `references/article-note.md`. Use this when the user already has a transcript Markdown file or pasted transcript and asks to refine notes from it. Work in the selected Markdown path when one is supplied. Prepend the note section above the existing transcript content, preserving the transcript below it. Do not route to a new path unless the user requests a copy or destination.
   - Audio downstream branch: read `references/audio-to-minutes.md` and `references/interview-polish.md`. Use this for ordinary podcast, video, and audio transcript polishing. First obtain the raw transcript, then assign one polishing subagent using the Polishing Plus Note Prompt Template. That single subagent polishes the raw transcript into Markdown, then adds the final audio Markdown packaging from `references/interview-polish.md` in the same Markdown file and returns the completed file path to the main thread. Use `references/interview-polish.md` filename rules for final Markdown. Audio download and Feishu Minutes steps may keep source or temporary filenames.
   - Direct-first-hand-note branch: read `references/audio-to-minutes.md` and `references/article-note.md`. Use this when the user provides first-hand source material such as a reading link, video, audio, or raw transcript and asks directly for a note or context note without asking for polished transcript prose. Obtain the source article or raw transcript, then prepend a note section to a single Markdown document containing the source content below it. Skip the interview-polish route.
     - Weibo status links: treat `m.weibo.cn/status/<id>`, `m.weibo.cn/detail/<id>`, and `weibo.com/.../<id>` as article inputs when the user asks for a note. Use the lightweight `weibo.cn/comment/<mblogid>` page as the default fetch path. For numeric status IDs,convert the decimal `mid` to the base62 `mblogid` by splitting from the right into 7-digit chunks,base62-encoding each chunk with alphabet `0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ`,left-padding every non-leading encoded chunk to 4 characters,and joining the chunks. Extract the original post from the first `div` whose id begins with `M_`,usually the nested `span.ctt`; ignore login prompts,refresh links,repost/comment/like controls,and comment blocks whose ids begin with `C_`.
   - Event transcript branch: read `references/event-transcript.md` before assigning or performing polishing. Use `references/event-transcript.md` filename rules for final Markdown.
3. Raw transcript handoff gate.
   - Once raw transcript files exist, the main agent must stop content drafting for ordinary podcast, video, and audio polished transcript delivery.
   - The main agent must assign one polishing subagent per podcast, video, or audio transcript using the Polishing Plus Note Prompt Template. The same polishing subagent handles both steps: polish first, then add final audio Markdown packaging, then return the completed path to the main thread.
   - For existing-transcript-to-note and direct-first-hand-note branches, note extraction is the requested final format. The main agent may create or insert the note section directly after reading `references/article-note.md`, and must skip polishing unless the user asks for polished transcript prose.
   - The main agent must not create summaries, notes, outlines, excerpt cards, or rewritten Markdown itself unless the user explicitly asks for that format instead of polished transcript prose.
   - Feishu Minutes AI summaries, platform caption dumps, and cleaned transcript text are intermediate artifacts for ordinary polished transcript delivery. For direct-first-hand-note requests, raw transcript text may remain as source content below the note section in the merged Markdown document.
4. Start polishing only after raw transcript files exist.
   - Use subagents for polishing and content work by default.
   - Start one polishing subagent per transcript.
   - Give each subagent exactly one raw transcript path, one output Markdown path, and the relevant bundled skill/reference paths.
   - Tell each subagent to read the full referenced skill files before editing.
   - Keep each subagent context independent.
5. Add final audio Markdown packaging inside the polishing subagent.
   - For ordinary podcast, video, or audio polishing, the single polishing subagent first creates the polished Markdown file.
   - The same subagent then builds `## 笔记` from the polished transcript body according to `references/interview-polish.md`.
   - The subagent must not fetch media again, transcribe audio again, create a new archive package, or split the source into separate files.
   - The subagent edits the polished Markdown in place unless the user gave a distinct final output path, then replies with the completed Markdown path only.
6. Deliver.
   - Apply the Global Obsidian Path Router to every final Markdown output before delivery, except when editing an existing user-selected Markdown file in place.
   - Apply filename rules from the active branch reference. When source metadata such as author, interviewee, company, organizer, title, or date is already available, pass it into the output path or subagent prompt before handoff. If metadata is missing, let the subagent infer the final filename from the source it is already reading and return the completed Markdown path. Do not do a second full-content read in the main thread when a subagent has already produced and named the final Markdown.
   - For note tasks, confirm the final Markdown has the note section at the very top, before the source article, source transcript, or polished transcript.
   - For video/audio inputs, final Markdown means polished Chinese media interview Markdown based on the transcript with `## 笔记` packaged at the top, unless the user explicitly asks for first-hand source notes, extraction notes, or another alternate format.
   - Confirm each expected Markdown file exists at the requested or routed path.
   - For all subagent-created Markdown, including ordinary interview outputs and event transcript outputs, the main agent only verifies file existence unless the user explicitly asks for review, excerpting, or debugging.

## Polishing Prompt Template

Use this shape when assigning an ordinary interview-polish subagent:

```text
Use the interview-polish skill to turn <raw transcript path> into polished Chinese media interview Markdown.

Skill path:
references/interview-polish.md

First read the full skill file, then follow its rules exactly. This meta skill is only orchestration context and does not override interview-polish.

Output path: <absolute output path>.

Use `references/interview-polish.md` filename rules if the provided output path is temporary or generic. You are only responsible for this file. Do not edit other files. When done, reply with the completed output path only.
```

For event transcripts, use the event-specific prompt in `references/event-transcript.md`.

## Polishing Plus Note Prompt Template

Use this shape when assigning an ordinary podcast, video, or audio interview-polish subagent:

```text
Use the interview-polish skill to turn <raw transcript path> into polished Chinese media interview Markdown with an Obsidian-ready note section at the top.

Skill path:
references/interview-polish.md

First read the full skill file. Follow interview-polish first to create the polished transcript Markdown. Then apply its final Markdown packaging rules to the polished Markdown.

Important boundaries:
- Do not fetch media or create Feishu Minutes.
- Use the raw transcript only for the polishing step.
- After polishing, use only the polished Markdown file to build the note section.
- Insert or replace `## 笔记` immediately below the top-level title.
- Preserve the polished transcript body below the note section.
- Use `## 正文` before the polished transcript body unless the body already has a clearer first heading.
- Edit the polished Markdown file in place unless a separate final output path is provided.

Output path: <absolute output path>.

Use `references/interview-polish.md` filename rules if the provided output path is temporary or generic. You are only responsible for this file. Do not edit other files. When done, reply with the completed Markdown path only.
```

## Orchestration Rules

- The user's request to process multimodal material is enough authorization to delegate the content-writing portion.
- Do not start polishing subagents before transcription is ready.
- Do not ask the main thread to rewrite or review the content after subagents finish.
- Do not paste large transcript chunks into the main thread. Pass file paths to subagents.
- Do not open or read final Markdown outputs from subagents unless the user explicitly requests review, excerpting, or debugging.
- For podcast, video, or audio requests, assign one polishing subagent to handle both polishing and final audio Markdown packaging through `references/interview-polish.md`. The main thread resumes only after that subagent returns the completed path.
- Keep status updates short. Report only source tokens, links, readiness state, and file paths during long waits.
- If a subagent output seems incomplete, send the subagent the relevant raw transcript time range or line range and the target file path. Avoid giving the whole transcript again.

## Wrong Path Examples

Do not:

- Treat platform captions or Feishu Minutes transcript text as finished Markdown for ordinary polished transcript delivery.
- Turn video/audio transcripts into summary cards, topic notes, or outlines in the main thread when the user requested this skill without an explicit alternate format.
- Create a standalone note document for podcast, video, or audio outputs. Insert the note as the first section of the same transcript Markdown instead.
- Run interview-polish before note extraction when the user directly asked for first-hand source notes from an article, reading link, video, audio, or raw transcript.
- Start a separate note subagent for audio final Markdown packaging. The single polishing subagent handles polishing and then note packaging.
- Let the article-note route perform end-to-end transcription or raw transcript polishing for podcast, video, or audio requests. Audio final Markdown packaging lives in `references/interview-polish.md`.
- Use Feishu Minutes AI summary as the final Markdown output.
- Skip polishing subagents after raw transcript readiness when the user requested ordinary polished transcript delivery.
- Open or rewrite subagent final Markdown in the main thread for ordinary delivery checks.
