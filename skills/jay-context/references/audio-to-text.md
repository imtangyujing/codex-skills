# Audio and Video to Text

Acquire every URL-based media source locally before ASR. Submit only local audio to Doubao Flash with Base64. Doubao Flash is the only ASR route;when it fails,report the failure instead of using the standard async API or another engine.

## Contract

```text
source media
→ YouTube or Bilibili: try one cookie-authenticated platform caption track first
→ platform caption success: create a temporary source transcript,convert it to output_language,then stop before ASR
→ platform caption failure or any other audio/video source: use local audio
→ download URL media locally
→ inspect local size and duration
→ normalize files at or above 20MiB to 16kHz mono 64kbps MP3
→ split files longer than 2 hours into non-overlapping 110-minute segments
→ submit each local file or segment to Doubao Flash with Base64
→ merge segment results and globalize timestamps
→ create temporary response JSON and source transcript
→ convert transcript semantics to output_language
→ validate the converted working transcript
→ replace source-language text artifacts with content-free processing status
→ remove generated compressed and segment files after complete success
→ continue in the same source owner with the selected text rules
```

The completed text stage ends when both persistent artifacts exist:

- `<slug>-transcript.<output_language>.txt`
- `<slug>-processing-status.json`

The processing-status file may contain engine,request IDs,Log IDs,timing,source-language detection,output language,attempt state,and failure metadata. It must not contain source-language transcript text or raw response bodies.

Do not polish,summarize,package notes,or choose the final Obsidian filename before the converted transcript passes validation.

## Credentials

On macOS,store the API key in the login Keychain:

```bash
security add-generic-password \
  -a 'jay-context' \
  -s 'DOUBAO_ASR_API_KEY' \
  -U -w
```

The helper reads credentials in this order:

1. `--api-key-file <path>`
2. `DOUBAO_ASR_API_KEY`
3. macOS Keychain item with account `jay-context` and service `DOUBAO_ASR_API_KEY`

When Jay-Context runs inside Myoo,configure the Doubao key under Myoo Settings → 语音识别. Myoo supplies it through `DOUBAO_ASR_API_KEY`.

Never put the key in `SKILL.md`,shell history,command arguments,logs,generated Markdown,or diagnostic manifests.

Default service values:

- Flash endpoint: `https://openspeech.bytedance.com/api/v3/auc/bigmodel/recognize/flash`
- Flash resource ID: `volc.bigasr.auc_turbo`
- Auth header: `X-Api-Key`
- Request ID: one fresh UUID per Flash segment
- HTTP timeout: 600 seconds to allow large Base64 uploads and Flash processing

## Local Acquisition

Use the first available faithful text or media source:

1. Page-provided verbatim transcript.
2. For YouTube,one usable manual or automatic caption track fetched with `yt-dlp --cookies-from-browser chrome`.
3. For Bilibili,Chinese AI captions fetched directly with `yt-dlp --cookies-from-browser chrome --skip-download --write-subs --sub-langs ai-zh --sub-format srt`.
4. Locally downloaded direct media URL.
5. Locally downloaded podcast enclosure from RSS,Simplecast,or ordinary HTML.
6. Locally downloaded media from another `yt-dlp`-supported page,or from YouTube or Bilibili after its cookie-authenticated caption attempt fails.
7. User-provided local media.

Platform routing is fixed:

- YouTube always attempts the browser-cookie caption route before downloading audio.
- Bilibili always requests `ai-zh` SRT captions with browser cookies before downloading audio. Do not gate this request on the `subtitles` or `automatic_captions` maps from `--dump-single-json`;authenticated `--list-subs` and direct subtitle download may work even when those maps are empty.
- Successful platform captions are downloaded as temporary source artifacts,converted to `source-captions-transcript.<output_language>.txt`,then removed with any source-language caption metadata after validation. Persist only content-free processing status. This route reports `doubao_attempted: false`.
- YouTube and Bilibili use local audio plus Doubao Flash only after their caption route fails.
- Other audio/video sources go directly to local media acquisition and Doubao Flash.
- The default browser-cookie source is Chrome. Set `JAY_CONTEXT_YTDLP_COOKIE_BROWSER` only when the active platform login lives in another yt-dlp-supported browser profile.

For URL sources:

- Use `yt-dlp --no-playlist -f bestaudio` for supported platform pages.
- Download direct media URLs to `source-media.<ext>`.
- Resolve RSS,Simplecast,and HTML media URLs only for local download.
- Save only content-free acquisition metadata as `source-media.info.json`;remove caption text,transcript fields,and signed URLs.
- Preserve the downloaded `source-media.<ext>` after ASR completion.
- Never send a public URL,temporary signed URL,cookie-dependent URL,or hosted copy to Doubao.

## Flash Preprocessing

Inspect every local file with `ffprobe` before submission.

- Files smaller than 20MiB,in a Flash-supported audio format,and no longer than 2 hours may be submitted unchanged.
- Files at or above `20 × 1024 × 1024` bytes must be normalized to 16kHz mono 64kbps MP3.
- Unsupported audio or video containers must be normalized even when smaller than 20MiB.
- Files longer than 2 hours must be normalized and split into non-overlapping 110-minute MP3 segments.
- Exactly 2 hours does not trigger segmentation.
- Every prepared segment must remain within the Flash limits of 2 hours and 100MiB.

Generated compressed files,segments,source-language transcript text,and ASR response bodies live temporarily in the task output directory. Remove them after every segment succeeds,the converted transcript passes validation,and content-free processing status exists. On failure,remove source-language text and raw response bodies,keep only content-free diagnostics and the failure manifest,and report that the task cannot produce a final Markdown file.

## Run

Default route for podcast,video,direct media URL,platform page,or local media:

```bash
python3 scripts/transcribe_media.py "<source>" \
  --output-dir "~/Downloads/<source-slug>"
```

Direct local Flash diagnostics:

```bash
python3 scripts/doubao_asr.py "/absolute/path/audio-or-video" \
  --output-dir "~/Downloads/<source-slug>"
```

Inspect a local file without sending it:

```bash
python3 scripts/doubao_asr.py "/absolute/path/audio-or-video" \
  --output-dir "~/Downloads/<source-slug>" \
  --dry-run
```

For a URL dry run,`transcribe_media.py --dry-run` reports the planned platform route without downloading captions or media. YouTube and Bilibili report the browser-cookie caption attempt and audio/Doubao fallback separately.

## Defaults

The helper sends:

- `model_name: bigmodel`
- `enable_itn: true`
- `enable_punc: true`
- `enable_ddc: false`
- `show_utterances: true`
- `enable_speaker_info: false`
- `enable_channel_split: false`
- `vad_segment: false`

Use `--speaker-info` for interviews,panels,and multi-speaker meetings when speaker separation is useful. Speaker identifiers are preserved per segment and are not remapped across segment boundaries. Use `--no-punc` only when downstream processing explicitly needs unpunctuated text.

## Segment Output

- A single-file run may temporarily create the raw Doubao response required to extract text. Remove it after converted-text validation.
- A segmented run may temporarily create a merged response containing transcript text and utterances. Remove response bodies after converted-text validation;retain only segment index,time range,request ID,Log ID,and attempt state in processing status.
- Offset utterance and word timestamps by each segment's start time.
- Merge transcript text in source order without overlapping segments.
- Return `mode: local-base64-flash` for one request and `mode: local-base64-flash-segmented` for multiple requests.
- Return `engine: doubao-flash-asr` from the acquisition wrapper.

If a segment fails,do not create or update the final converted transcript. Stop the run,remove source-language response bodies,and write a content-free `<slug>-asr-failure.json`.

## Converted Transcript Format

- Prefer `result.utterances` when present.
- Preserve utterance order.
- Include speaker labels when returned.
- Include timestamps by default;use `--plain-text` only when downstream tooling requires clean lines.
- Fall back to `result.text` when utterances are absent.
- Translate semantic text faithfully into `output_language` before persistence. Preserve speaker identity,order,timestamps,numbers,technical terms,and proper names.
- Keep content-free processing status as the audit source.

## Downstream Continuation

- Ordinary podcast/video/audio: the current source owner reads `references/interview-polish.md`,polishes the converted transcript,and packages the localized notes section in the same final Markdown.
- Direct note/context request: the current source owner uses the converted transcript as source content for `references/article-note.md`.
- Event transcript: the current source owner applies `references/event-transcript.md` and `references/interview-polish.md`.
- Converted transcript readiness does not trigger a new agent. Do not call `spawn_agent`.

## No-Feishu and No-Fallback Rule

Do not call:

- `lark-cli drive +upload`
- `lark-cli minutes +upload`
- `lark-cli vc +notes`

Do not call the Doubao standard async submit/query endpoints. Do not use `--public-url`,polling,resume IDs,Feishu Minutes,or another ASR fallback. When credentials,submission,format,size,duration,or permissions fail,report the failure.
