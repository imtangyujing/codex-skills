# Audio to Feishu Minutes

Read this reference for internet video/audio, podcast pages, RSS episodes, direct MP3 links, local recordings, Feishu Drive upload, Feishu Minutes creation, transcript polling, and low-bitrate source audio selection.

## Source Audio

- Prefer platform metadata and direct audio tracks over screen recording.
- Select the lowest available audio bitrate by default.
- Do not choose the highest quality track for transcription-only work unless the user explicitly asks for an archival-quality audio file.
- If the platform only exposes one audio track, use that track.
- Save source audio under `~/Downloads` unless the user asks for another working folder.

## YouTube

For YouTube links, use local browser cookies by default when reading metadata, listing subtitles, downloading platform captions, or downloading transcription audio. This avoids the common sign-in and bot-check gate before work starts.

Use Chrome cookies first:

```bash
yt-dlp --cookies-from-browser chrome --no-playlist ...
```

If Chrome cookies are unavailable, try the user's active browser cookies, such as Safari or Firefox, before falling back to a no-cookie request.

Always add `--no-playlist` when the user provides a single YouTube video URL that contains playlist parameters such as `list=WL` or `index=...`.

When the task only needs metadata, subtitle listing, or subtitle download, add `--ignore-no-formats-error` by default. Some YouTube videos expose usable metadata and automatic captions while yt-dlp still reports `Only images are available for download` or `Requested format is not available` because video/audio format extraction hit the YouTube `n challenge`. In that situation, do not retry a plain metadata command first; keep going with subtitle extraction if captions are listed.

Use this metadata command for caption-first workflows:

```bash
yt-dlp --cookies-from-browser chrome --no-playlist --skip-download --ignore-no-formats-error --dump-json "<youtube url>" -o '%(id)s.%(ext)s'
```

Use this subtitle-listing command:

```bash
yt-dlp --cookies-from-browser chrome --no-playlist --skip-download --ignore-no-formats-error --list-subs "<youtube url>"
```

Prefer platform captions first:

```bash
yt-dlp --cookies-from-browser chrome --no-playlist --skip-download --ignore-no-formats-error --write-subs --write-auto-subs --sub-langs 'en.*,en,zh.*,zh' --sub-format srt --convert-subs srt -o '%(id)s.%(ext)s' "<youtube url>"
```

If usable captions are unavailable, download the lowest practical audio track with local browser cookies and continue through Feishu Minutes transcription.

For Bilibili DASH audio, sort `dash.audio` by `bandwidth` ascending and download the first usable track:

```python
audio = min(playurl["data"]["dash"]["audio"], key=lambda item: item.get("bandwidth", 10**12))
```

Download `audio["baseUrl"]` with a Bilibili video `Referer` header, upload that file with `lark-cli drive +upload`, then create Minutes with `lark-cli minutes +upload`.

## Podcast and Direct MP3

For podcast pages and direct MP3 links, run the bundled script from the skill folder:

```bash
python3 scripts/podcast_to_minutes.py "<podcast episode URL>" --output-dir ~/Downloads
```

The script resolves the audio URL from Simplecast API, RSS feed, direct `.mp3`, or HTML page with embedded audio. It downloads the MP3, runs `lark-cli drive +upload`, runs `lark-cli minutes +upload`, and prints JSON with `mp3_path`, `file_token`, `drive_url`, `minute_url`, and `minute_token` when the token can be detected.

If the resolver fails, inspect the page manually for RSS feed metadata or embedded audio URLs, then patch or bypass the script with a direct MP3 URL.

## Feishu Upload and Scopes

Treat the user's request to put a source into Feishu Minutes as confirmation for Drive upload and Minutes creation.

Required Feishu scopes:

- `drive:file:upload`
- `minutes:minutes.upload:write`

If `lark-cli` returns `missing_scope`, start the exact auth command from the CLI hint, wait for the user to approve the browser or device link, then rerun.

## Transcript Polling

- Do not fetch transcripts or AI summaries until the Minutes record exists.
- When the transcript is needed, poll with:

```bash
lark-cli vc +notes --minute-tokens <minute_token>
```

- Keep polling output compact. Report only tokens, links, ready/not-ready state, and file paths.
- Save raw transcripts to local files before polishing.
- If the transcript is not ready, wait and poll again instead of starting polishing.

## Transcript Delivery

When the user asks for Markdown delivery, this reference only prepares the audio source and raw transcript:

- Save raw transcript under a temporary or source-specific working folder.
- Return or pass the raw transcript path to the parent workflow.
- Keep audio downloads, Drive uploads, Minutes records, and raw transcript files under source or temporary filenames.

Do not decide final Markdown filenames, write polished content, add `## 笔记`, or package the transcript body here. Final interview-style Markdown content, note packaging, delivery checks, and filenames live in `references/interview-polish.md`.
