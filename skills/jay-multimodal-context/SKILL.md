---
name: jay-multimodal-context
description: Convert multimodal source material into usable writing context, especially internet video/audio links, local recordings, Feishu Minutes transcripts, or raw Chinese interview transcripts that need polished interview-style Markdown. Use when the user provides Bilibili/video/podcast/audio links and asks for transcription plus interview polishing, or when the user already has raw transcript text and wants interview-polish output. This skill combines low-bitrate source audio retrieval, Feishu Minutes transcription, and interview-polish editing while keeping orchestration, transcription, and polishing responsibilities separate.
---

# Jay-Multimodal-Context

## Overview

Use one workflow for two entry points:

- Internet video/audio or local recording: extract the lowest practical source audio, upload to Feishu Minutes, wait for raw transcript, then polish.
- Existing raw transcript: skip audio and transcription, then polish directly.

The main agent is the orchestrator. It assigns work, waits for artifacts, and checks delivery paths. It does not rewrite interview content when subagents are available.

This skill is self-contained and portable. It bundles its resources inside this folder:

- `references/interview-polish/SKILL.md` — the polishing skill. Read it in full before any polishing work.
- `scripts/podcast_to_minutes.py` — fetches podcast/MP3 audio and creates a Feishu Minutes record.

Resolve all relative paths from the directory containing this `SKILL.md`.

Default local workspace:

- Use the user's Downloads folder, `~/Downloads`, as the working and delivery root unless the user explicitly asks for another folder.
- Create source-specific subfolders under `~/Downloads` only when needed to keep raw audio, raw transcripts, and final Markdown easy to distinguish.
- Do not create or reuse a `multimodal-context` folder in the current repository/workspace unless the user explicitly requests that path.

## Workflow

1. Identify the input type.
   - Video/audio links include Bilibili, podcast pages, RSS episodes, direct MP3/M4A files, and local recordings.
   - Raw transcript inputs include timestamped text, speaker-labeled text, Feishu Minutes text, or files containing rough interview dialogue.
   - Event transcripts include mixed venue chatter, host introductions, prepared talks, roundtables, audience Q&A, and post-event side conversations. Treat these as a distinct source type instead of forcing everything into an interview.
2. For video/audio input, obtain the audio file.
   - Prefer platform metadata and direct audio tracks over screen recording.
   - Select the lowest available audio bitrate by default. For Bilibili DASH audio, sort `dash.audio` by `bandwidth` ascending and download the first usable track.
   - For podcast pages and direct MP3 links, use the bundled `scripts/podcast_to_minutes.py` helper (see Audio to Feishu Minutes below), which both downloads the audio and creates the Minutes record.
   - Do not choose the highest quality track for transcription-only work unless the user explicitly asks for an archival-quality audio file.
   - If the platform only exposes one audio track, use that track.
3. Upload audio to Feishu.
   - Upload the lowest-source audio file to Feishu Drive and create Feishu Minutes.
   - Keep the original downloaded source audio only as a temporary working artifact unless the user asks to retain it.
4. Wait until Feishu Minutes transcript is ready.
   - Poll with minutes/VC notes commands until the transcript is available.
   - Keep polling output compact. Report only tokens, links, ready/not-ready state, and file paths.
   - Save raw transcripts to local files before polishing.
5. Start polishing only after raw transcript files exist.
   - When polishing or other content work is needed, start the appropriate polishing subagent yourself. Do not wait for separate user approval.
   - For every transcript that needs polished Markdown, start one polishing subagent per transcript.
   - Give each subagent exactly one raw transcript path, one output Markdown path, and the bundled interview-polish skill path (`references/interview-polish/SKILL.md`).
   - Tell each subagent to read the full skill before editing. Do not summarize or partially copy the skill rules.
   - Keep each subagent context independent. Do not ask one subagent to share context with another.
6. Main-agent delivery check.
   - Confirm each expected Markdown file exists at the requested path.
   - Do not read the subagent's delivered Markdown in the main thread unless the user explicitly asks for review, excerpting, or debugging.
   - Do not run forbidden-phrase, quote-style, formatting, or content-level self-review checks in the main thread unless the user explicitly asks.
   - If a subagent reports completion and the output file exists, treat the delivery as complete.

## Event Transcript Special Case

Use this branch when a transcript comes from a salon, meetup, panel, workshop, conference sharing, roadshow, or similar event.

First classify segments by function:

- Venue chatter: logistics, seat changes, microphone checks, greetings, and food plans. Drop these unless they contain substantive industry views, named claims, useful facts, or questions that frame later content.
- Pre-event and post-event side conversations: keep substantive private exchanges as standalone sections, usually titled `#### ####会前交流：...` or `#### ####会后追问：...`. If a speaker identity is uncertain, label the speaker as `观众` instead of guessing a guest name.
- Host opening and transitions: polish lightly and keep only the framing, topic setup, guest introductions, and section transitions that help the reader understand the event.
- Prepared talks or presentations: preserve the speaker's first-person voice. Do not convert these into third-person summaries and do not invent an interviewer role. Format as `SpeakerName：...` followed by polished first-person paragraphs.
- Roundtables, audience Q&A, and media follow-ups: use the interview-polish Q&A style. Questions may be attributed to the host, `量子位`, `现场提问`, or `观众` when identity is unclear.

For event transcripts, the final Markdown should normally follow the source event order:

1. Substantive pre-event side conversations.
2. Host opening and context.
3. Each guest's prepared talk, with one section per speaker.
4. Roundtable discussion.
5. Audience Q&A.
6. Substantive post-event side conversations or follow-up questions.

Do not compress a prepared talk into a third-party recap such as `X提到...` or `X认为...` when the source is the speaker's own presentation. Prefer direct first-person polished prose such as `崔昊天：我比较看重...`.

Do not assign a name to an early or side-channel speaker just because the same speaker number later maps to a named guest. Feishu speaker IDs can drift or capture nearby audience conversations. When identity is uncertain, use `观众`.

Before delivery, mechanically check event outputs for:

- Guest names the user supplied, including exact Chinese characters.
- Residual placeholder labels such as `Speaker 1`.
- Misheard names from transcript captions.
- The user's standing style constraints, such as forbidden sentence patterns and quote style.

## Polishing Prompt Template

Use this shape when assigning a polishing subagent:

```text
Use the interview-polish skill to turn <raw transcript path> into polished Chinese media interview Markdown.

Skill path:
references/interview-polish/SKILL.md

First read the full skill file, then follow its rules exactly. This meta skill is only orchestration context and does not override interview-polish.

Output path: <absolute output path>.

You are only responsible for this file. Do not edit other files. When done, reply with the output path only.
```

## Orchestration Rules

- Use subagents for polishing and content work by default. The user's request to process multimodal material is enough authorization to delegate the content-writing portion.
- Do not start polishing subagents before transcription is ready.
- Do not ask the main thread to rewrite or review the content after subagents finish. The main thread checks file existence only, unless the user explicitly requests additional checks.
- Do not paste large transcript chunks into the main thread. Pass file paths to subagents.
- Do not open or read final Markdown outputs from subagents just to inspect quality or policy details. That review belongs to the subagent unless the user explicitly requests a second pass.
- Keep status updates short. Long waits do not cost much; large pasted evidence does.
- If a subagent output seems incomplete, send the subagent the relevant raw transcript time range or line range and the target file path. Avoid giving the whole transcript again.

## Bundled Resources

- `references/interview-polish/SKILL.md`
  - Use for all transcript polishing, formatting, language cleanup, and media interview prose conversion.
  - Always read the full file before assigning or performing polishing work.
- `scripts/podcast_to_minutes.py`
  - Helper for podcast pages and direct MP3 links: downloads the audio, uploads it to Feishu Drive, and creates a Minutes record.
  - For platform video such as Bilibili, prefer the low-bitrate source-audio rule below instead of this script.

## Audio to Feishu Minutes

For podcast pages and direct MP3 links, run the bundled script:

```bash
python3 scripts/podcast_to_minutes.py "<podcast episode URL>" --output-dir ~/Downloads
```

The script resolves the audio URL (Simplecast API, RSS feed, direct `.mp3`, or HTML page with embedded audio), downloads the MP3, runs `lark-cli drive +upload` then `lark-cli minutes +upload`, and prints JSON with `mp3_path`, `file_token`, `drive_url`, and `minute_url`.

Required Feishu scopes:

- `drive:file:upload`
- `minutes:minutes.upload:write`

If `lark-cli` returns `missing_scope`, start the exact auth command from the CLI hint, wait for the user to approve the browser/device link, then rerun.

For platform video with multiple audio tracks, choose the lowest bitrate track before uploading. For Bilibili, the selection rule is:

```python
audio = min(playurl["data"]["dash"]["audio"], key=lambda item: item.get("bandwidth", 10**12))
```

Then download `audio["baseUrl"]` with a Bilibili video `Referer` header, upload that file with `lark-cli drive +upload`, and create Minutes with `lark-cli minutes +upload`.

Defaults:

- Save source audio, raw transcripts, and final Markdown under `~/Downloads` unless the user asks for another folder. Use readable filenames derived from the title.
- Treat the user's request to put a source into Feishu Minutes as confirmation for the Drive upload and the Minutes creation.
- Do not fetch transcripts or AI summaries until the Minutes record exists. When the transcript is needed, poll with `lark-cli vc +notes --minute-tokens <token>`.
- If the podcast resolver fails, inspect the page manually for RSS feed metadata or embedded audio URLs, then patch or bypass the script with a direct MP3 URL.

When the user asks for Markdown delivery, save both:

- Raw transcript under a temporary or source-specific working folder.
- Final polished Markdown under the user-requested folder.
