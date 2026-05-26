---
name: yt-dlp-mp3
description: Convert video or audio URLs to MP3 files using yt-dlp on macOS. Use when the user asks to download audio, extract MP3, convert formats, or build a quick one-command workflow for YouTube (or similar) links.
---

# YT-DLP MP3

## Overview
Provide a fast, copy-pasteable command to extract MP3 audio with yt-dlp and save to the user's chosen folder (default: `~/Downloads`).

## Workflow

### 1) Confirm requirements
- Require `yt-dlp` in PATH.
- Recommend `ffmpeg` for MP3 conversion (without it, yt-dlp may download video only).

### 2) One-link MP3 download
Use this as the default command:

```bash
yt-dlp -x --audio-format mp3 --audio-quality 0 -o "$HOME/Downloads/%(title)s.%(ext)s" "<URL>"
```

### 3) Useful variants
- Save in the current folder:

```bash
yt-dlp -x --audio-format mp3 --audio-quality 0 -o "%(title)s.%(ext)s" "<URL>"
```

- Download a playlist (one MP3 per item):

```bash
yt-dlp -x --audio-format mp3 --audio-quality 0 -o "$HOME/Downloads/%(playlist)s/%(title)s.%(ext)s" "<PLAYLIST_URL>"
```

- Choose a specific title format:

```bash
yt-dlp -x --audio-format mp3 --audio-quality 0 -o "$HOME/Downloads/%(uploader)s - %(title)s.%(ext)s" "<URL>"
```

### 4) If MP3 still does not appear
- Explain that `ffmpeg` is missing or not in PATH.
- Ask whether to install `ffmpeg` (provide a minimal, user-approved install path).

## Notes
- Encourage only downloading content the user is authorized to download and use.
