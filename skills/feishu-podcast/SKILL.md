---
name: feishu-podcast
description: Download a podcast episode from a user-provided podcast URL, save the MP3 locally, upload it to Feishu Drive, and create a Feishu Minutes record. Use when the user gives a podcast/episode link and asks to download audio, put it into Feishu Minutes/Miaojì, transcribe it, or create a meeting-note style asset from the podcast.
---

# Feishu Podcast

## Workflow

Use the bundled script first:

```bash
python3 ~/.codex/skills/feishu-podcast/scripts/podcast_to_minutes.py "<podcast episode URL>" --output-dir .
```

The script:

1. Resolves the audio URL from common podcast pages.
   - Simplecast episode URLs via `https://api.simplecast.com/episodes/search`.
   - Direct `.mp3` URLs.
   - RSS feeds and HTML pages with RSS or MP3 links.
2. Downloads the audio as an `.mp3` file.
3. Runs `lark-cli drive +upload --file <mp3>` to get `file_token`.
4. Runs `lark-cli minutes +upload --file-token <file_token>` to create the Feishu Minutes link.
5. Prints JSON with `mp3_path`, `file_token`, `drive_url`, and `minute_url`.

## Required Feishu Permissions

The Feishu upload path needs these scopes:

- `drive:file:upload`
- `minutes:minutes.upload:write`

If `lark-cli` returns `missing_scope`, start the exact auth command from the CLI hint, wait for the user to approve the browser/device link, then rerun the script.

## Defaults

- Save the MP3 in the current working directory unless the user asks for another folder.
- Use a readable filename derived from the podcast title.
- Do not fetch transcripts, AI summaries, or edit the generated document unless the user explicitly asks after the Minutes link exists.
- If the user asks for transcript or summary next, use the generated `minute_url` token with `lark-cli vc +notes --minute-tokens <token>`.

## Notes

- This is a write workflow: it uploads a file to Feishu Drive and creates a Feishu Minutes asset. Treat the user's request to "put it into Feishu Minutes" as confirmation for these two writes.
- If the podcast resolver fails, inspect the page manually for RSS feed metadata or embedded audio URLs, then patch or bypass the script with a direct MP3 URL.
