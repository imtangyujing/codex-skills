#!/usr/bin/env python3
"""Acquire media locally and transcribe it with Doubao Flash ASR."""

from __future__ import annotations

import argparse
import html
import json
import os
import re
import shutil
import subprocess
import sys
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent
DOUBAO_SCRIPT = Path(
    os.environ.get("JAY_CONTEXT_DOUBAO_SCRIPT", SCRIPT_DIR / "doubao_asr.py")
)
DIRECT_MEDIA_SUFFIXES = {
    ".aac",
    ".flac",
    ".m4a",
    ".m4s",
    ".mkv",
    ".mov",
    ".mp3",
    ".mp4",
    ".mpeg",
    ".mpg",
    ".ogg",
    ".opus",
    ".wav",
    ".webm",
}
PLATFORM_HOSTS = {
    "b23.tv",
    "bilibili.com",
    "soundcloud.com",
    "twitter.com",
    "vimeo.com",
    "x.com",
    "youtu.be",
    "youtube.com",
}
YOUTUBE_HOSTS = {
    "youtu.be",
    "youtube.com",
}
BILIBILI_HOSTS = {
    "b23.tv",
    "bilibili.com",
}
YOUTUBE_COOKIE_BROWSER = "chrome"
CAPTION_LANGUAGE_PREFERENCES = (
    "zh-Hans",
    "zh-CN",
    "zh-Hant",
    "zh-TW",
    "zh",
    "en",
    "en-US",
    "en-GB",
)
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X) jay-context/1.0"


def run(command: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, text=True, capture_output=True)


def parse_payload(process: subprocess.CompletedProcess[str]) -> dict[str, Any]:
    raw = process.stdout.strip() if process.returncode == 0 else process.stderr.strip()
    if not raw:
        return {}
    try:
        value = json.loads(raw)
    except json.JSONDecodeError:
        return {"error": raw[-1600:]}
    return value if isinstance(value, dict) else {"error": raw[-1600:]}


def append_option(command: list[str], flag: str, value: Any) -> None:
    if value is not None:
        command.extend([flag, str(value)])


def is_url(source: str) -> bool:
    parsed = urllib.parse.urlparse(source)
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)


def is_direct_media_url(source: str) -> bool:
    return is_url(source) and Path(urllib.parse.urlparse(source).path).suffix.lower() in (
        DIRECT_MEDIA_SUFFIXES
    )


def host_matches(source: str, hosts: set[str]) -> bool:
    if not is_url(source):
        return False
    host = (urllib.parse.urlparse(source).hostname or "").lower()
    return any(host == item or host.endswith(f".{item}") for item in hosts)


def is_platform_page(source: str) -> bool:
    return host_matches(source, PLATFORM_HOSTS)


def is_youtube_url(source: str) -> bool:
    return host_matches(source, YOUTUBE_HOSTS)


def is_bilibili_url(source: str) -> bool:
    return host_matches(source, BILIBILI_HOSTS)


def youtube_cookie_browser() -> str:
    return (
        os.environ.get("JAY_CONTEXT_YTDLP_COOKIE_BROWSER", "").strip()
        or YOUTUBE_COOKIE_BROWSER
    )


def command_path(name: str, env_name: str) -> str:
    configured = os.environ.get(env_name, "").strip()
    if configured:
        path = Path(configured).expanduser()
        if path.exists():
            return str(path)
        raise RuntimeError(f"{env_name} points to a missing executable: {path}")
    found = shutil.which(name)
    if not found:
        raise RuntimeError(f"Required command is unavailable: {name}")
    return found


def request_bytes(url: str, timeout: float = 60.0) -> tuple[bytes, dict[str, str], str]:
    request = urllib.request.Request(url, headers={"User-Agent": UA})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return response.read(), dict(response.headers), response.geturl()
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"HTTP {exc.code} from {url}: {body[:500]}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"Request failed for {url}: {exc.reason}") from exc


def post_json(url: str, payload: dict[str, Any], timeout: float = 60.0) -> dict[str, Any]:
    request = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "User-Agent": UA,
            "Accept": "application/json",
            "Content-Type": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            value = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"HTTP {exc.code} from {url}: {body[:500]}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"Request failed for {url}: {exc.reason}") from exc
    if not isinstance(value, dict):
        raise RuntimeError(f"JSON response from {url} must be an object.")
    return value


def decode_text(raw: bytes, headers: dict[str, str]) -> str:
    content_type = next(
        (
            value
            for key, value in headers.items()
            if key.lower() == "content-type"
        ),
        "",
    )
    match = re.search(r"charset=([^;\s]+)", content_type, re.I)
    encoding = match.group(1) if match else "utf-8"
    return raw.decode(encoding, errors="replace")


def html_title(text: str) -> str | None:
    og = re.search(
        r'<meta[^>]+property=["\']og:title["\'][^>]+content=["\']([^"\']+)["\']',
        text,
        re.I,
    )
    if og:
        return html.unescape(og.group(1))
    title = re.search(r"<title[^>]*>(.*?)</title>", text, re.I | re.S)
    return re.sub(r"\s+", " ", title.group(1)).strip() if title else None


def parse_rss(raw: bytes, page_url: str) -> dict[str, str] | None:
    root = ET.fromstring(raw)
    channel_title = root.findtext("./channel/title") or "podcast"
    item = root.find("./channel/item")
    if item is None:
        return None
    enclosure = item.find("enclosure")
    if enclosure is None or not enclosure.attrib.get("url"):
        return None
    return {
        "media_url": urllib.parse.urljoin(page_url, enclosure.attrib["url"]),
        "title": item.findtext("title") or channel_title,
        "acquisition": "rss-enclosure",
    }


def simplecast_lookup(url: str) -> dict[str, str] | None:
    if "simplecast.com" not in urllib.parse.urlparse(url).netloc.lower():
        return None
    episode = post_json(
        "https://api.simplecast.com/episodes/search",
        {"url": url},
    )
    media_url = episode.get("enclosure_url")
    if not media_url:
        return None
    return {
        "media_url": media_url,
        "title": episode.get("title") or "podcast-episode",
        "acquisition": "simplecast-api",
    }


def resolve_page_media(url: str) -> dict[str, str]:
    simplecast = simplecast_lookup(url)
    if simplecast:
        return simplecast
    raw, headers, final_url = request_bytes(url)
    content_type = next(
        (
            value.lower()
            for key, value in headers.items()
            if key.lower() == "content-type"
        ),
        "",
    )
    if "xml" in content_type or raw.lstrip().startswith(b"<?xml"):
        rss = parse_rss(raw, final_url)
        if rss:
            return rss
    text = html.unescape(decode_text(raw, headers))
    media = re.search(
        r"https?://[^\"'<>\s]+\.(?:mp3|m4a|aac|wav|ogg|opus|flac)"
        r"(?:\?[^\"'<>\s]*)?",
        text,
        re.I,
    )
    if media:
        return {
            "media_url": media.group(0),
            "title": html_title(text) or "media",
            "acquisition": "html-media",
        }
    rss_link = re.search(
        r'<link[^>]+(?:type=["\']application/rss\+xml["\'][^>]+href=["\']'
        r'([^"\']+)["\']|href=["\']([^"\']+)["\'][^>]+type=["\']'
        r'application/rss\+xml["\'])',
        text,
        re.I,
    )
    if rss_link:
        rss_url = urllib.parse.urljoin(
            final_url, rss_link.group(1) or rss_link.group(2)
        )
        rss_raw, _, rss_final_url = request_bytes(rss_url)
        rss = parse_rss(rss_raw, rss_final_url)
        if rss:
            return rss
    raise RuntimeError("Page has no resolvable audio URL.")


def extension_for_url(url: str, headers: dict[str, str] | None = None) -> str:
    suffix = Path(urllib.parse.urlparse(url).path).suffix.lower()
    if suffix in DIRECT_MEDIA_SUFFIXES:
        return suffix
    content_type = ""
    if headers:
        content_type = next(
            (
                value.lower().split(";", 1)[0]
                for key, value in headers.items()
                if key.lower() == "content-type"
            ),
            "",
        )
    aliases = {
        "audio/aac": ".aac",
        "audio/flac": ".flac",
        "audio/mp4": ".m4a",
        "audio/mpeg": ".mp3",
        "audio/ogg": ".ogg",
        "audio/opus": ".opus",
        "audio/wav": ".wav",
        "video/mp4": ".mp4",
        "video/webm": ".webm",
    }
    return aliases.get(content_type, ".mp3")


def write_info_json(output_dir: Path, value: dict[str, Any]) -> None:
    (output_dir / "source-media.info.json").write_text(
        json.dumps(value, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def caption_language_rank(language: str, original_language: str | None) -> tuple[int, str]:
    normalized = language.lower()
    original = (original_language or "").lower()
    if original and normalized == original:
        return (0, normalized)
    if normalized.endswith("-orig"):
        return (1, normalized)
    for index, preferred in enumerate(CAPTION_LANGUAGE_PREFERENCES, start=2):
        if normalized == preferred.lower():
            return (index, normalized)
    if normalized.startswith("zh"):
        return (20, normalized)
    if normalized.startswith("en"):
        return (21, normalized)
    return (30, normalized)


def select_youtube_caption(info: dict[str, Any]) -> tuple[str, str]:
    original_language = info.get("language")
    if not isinstance(original_language, str):
        original_language = None
    for kind in ("subtitles", "automatic_captions"):
        captions = info.get(kind)
        if not isinstance(captions, dict):
            continue
        languages = [
            language
            for language, formats in captions.items()
            if isinstance(language, str)
            and language != "live_chat"
            and isinstance(formats, list)
            and formats
        ]
        if languages:
            language = min(
                languages,
                key=lambda value: caption_language_rank(value, original_language),
            )
            return kind, language
    raise RuntimeError("YouTube has no usable manual or automatic captions.")


def caption_timestamp(milliseconds: int) -> str:
    total_seconds = max(milliseconds, 0) // 1000
    hours, remainder = divmod(total_seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}"


def clean_caption_text(value: str) -> str:
    value = re.sub(r"<[^>]+>", "", value)
    value = html.unescape(value)
    return re.sub(r"\s+", " ", value).strip()


def json3_transcript(path: Path) -> str:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as exc:
        raise RuntimeError(f"Cannot read downloaded YouTube captions: {exc}") from exc
    events = payload.get("events") if isinstance(payload, dict) else None
    if not isinstance(events, list):
        raise RuntimeError("Downloaded YouTube JSON3 captions contain no events.")
    lines: list[str] = []
    previous_text = ""
    for event in events:
        if not isinstance(event, dict):
            continue
        segments = event.get("segs")
        if not isinstance(segments, list):
            continue
        text = clean_caption_text(
            "".join(
                segment.get("utf8", "")
                for segment in segments
                if isinstance(segment, dict)
                and isinstance(segment.get("utf8", ""), str)
            )
        )
        if not text or text == previous_text:
            continue
        start = event.get("tStartMs")
        start_ms = start if isinstance(start, int) else 0
        lines.append(f"[{caption_timestamp(start_ms)}] {text}")
        previous_text = text
    if not lines:
        raise RuntimeError("Downloaded YouTube captions contain no usable text.")
    return "\n".join(lines) + "\n"


def text_caption_transcript(path: Path) -> str:
    try:
        raw = path.read_text(encoding="utf-8-sig")
    except OSError as exc:
        raise RuntimeError(f"Cannot read downloaded YouTube captions: {exc}") from exc
    lines: list[str] = []
    previous_text = ""
    in_note = False
    current_timestamp: str | None = None
    for raw_line in raw.splitlines():
        line = raw_line.strip()
        if line.startswith(("NOTE", "STYLE", "REGION")):
            in_note = True
            continue
        if not line:
            in_note = False
            current_timestamp = None
            continue
        if in_note:
            continue
        if line in {"WEBVTT"} or line.isdigit():
            continue
        cue_time = re.match(
            r"(?:(\d+):)?(\d{2}):(\d{2})[.,]\d+\s+-->",
            line,
        )
        if cue_time:
            hours = int(cue_time.group(1) or 0)
            minutes = int(cue_time.group(2))
            seconds = int(cue_time.group(3))
            current_timestamp = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
            continue
        if "-->" in line:
            continue
        text = clean_caption_text(line)
        if not text or text == previous_text:
            continue
        lines.append(
            f"[{current_timestamp}] {text}"
            if current_timestamp
            else text
        )
        previous_text = text
    if not lines:
        raise RuntimeError("Downloaded YouTube captions contain no usable text.")
    return "\n".join(lines) + "\n"


def platform_caption_transcript(path: Path) -> str:
    if path.suffix.lower() == ".json3":
        return json3_transcript(path)
    return text_caption_transcript(path)


def find_caption_file(
    output_dir: Path,
    language: str,
) -> Path:
    caption_candidates = [
        path
        for path in output_dir.glob("source-captions.*")
        if path.name != "source-captions.info.json"
        and path.name != "source-captions-raw-transcript.txt"
        and path.suffix not in {".part", ".ytdl"}
    ]
    if not caption_candidates:
        raise RuntimeError(
            "Platform caption download completed without a caption file."
        )
    selected_language_candidates = [
        path for path in caption_candidates if f".{language}." in path.name
    ]
    return max(
        selected_language_candidates or caption_candidates,
        key=lambda path: path.stat().st_mtime_ns,
    )


def persist_platform_captions(
    source: str,
    output_dir: Path,
    caption_path: Path,
    info: dict[str, Any],
    platform: str,
    caption_kind: str,
    language: str,
    cookie_browser: str,
) -> dict[str, Any]:
    transcript = platform_caption_transcript(caption_path)
    transcript_path = output_dir / "source-captions-raw-transcript.txt"
    transcript_path.write_text(transcript, encoding="utf-8")
    caption_info_path = output_dir / "source-captions.info.json"
    caption_info_path.write_text(
        json.dumps(
            {
                "title": info.get("title"),
                "id": info.get("id"),
                "uploader": info.get("uploader"),
                "upload_date": info.get("upload_date"),
                "source_url": source,
                "platform": platform,
                "caption_kind": caption_kind,
                "caption_language": language,
                "browser_cookie_source": cookie_browser,
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    result = {
        "ok": True,
        "engine": f"{platform}-platform-captions",
        "mode": f"{platform}-captions-with-browser-cookies",
        "source_url": source,
        "title": info.get("title"),
        "platform": platform,
        "caption_kind": caption_kind,
        "caption_language": language,
        "browser_cookie_source": cookie_browser,
        "caption_path": str(caption_path.resolve()),
        "caption_info_path": str(caption_info_path.resolve()),
        "transcript_path": str(transcript_path.resolve()),
        "platform_captions_attempted": True,
        "doubao_attempted": False,
        "fallback_used": False,
    }
    result[f"{platform}_captions_attempted"] = True
    return result


def acquire_youtube_captions(
    source: str,
    output_dir: Path,
) -> dict[str, Any]:
    ytdlp = command_path("yt-dlp", "JAY_CONTEXT_YTDLP_BIN")
    cookie_browser = youtube_cookie_browser()
    info_command = [
        ytdlp,
        "--cookies-from-browser",
        cookie_browser,
        "--no-playlist",
        "--skip-download",
        "--ignore-no-formats-error",
        "--dump-single-json",
        "--no-warnings",
        source,
    ]
    info_process = run(info_command)
    if info_process.returncode != 0:
        detail = (info_process.stderr or info_process.stdout).strip()[-1200:]
        raise RuntimeError(
            f"Cookie-authenticated YouTube caption lookup failed: {detail}"
        )
    try:
        info = json.loads(info_process.stdout)
    except json.JSONDecodeError as exc:
        raise RuntimeError("YouTube caption lookup returned invalid metadata.") from exc
    if not isinstance(info, dict):
        raise RuntimeError("YouTube caption lookup returned invalid metadata.")
    caption_kind, language = select_youtube_caption(info)
    output_template = str(output_dir / "source-captions.%(ext)s")
    caption_command = [
        ytdlp,
        "--cookies-from-browser",
        cookie_browser,
        "--no-playlist",
        "--skip-download",
        "--no-warnings",
        "--sub-langs",
        f"^{re.escape(language)}$",
        "--sub-format",
        "json3/vtt/best",
        "--no-overwrites",
        "-o",
        output_template,
        "--write-subs" if caption_kind == "subtitles" else "--write-auto-subs",
        source,
    ]
    caption_process = run(caption_command)
    if caption_process.returncode != 0:
        detail = (caption_process.stderr or caption_process.stdout).strip()[-1200:]
        raise RuntimeError(
            f"Cookie-authenticated YouTube caption download failed: {detail}"
        )
    caption_path = find_caption_file(output_dir, language)
    return persist_platform_captions(
        source=source,
        output_dir=output_dir,
        caption_path=caption_path,
        info=info,
        platform="youtube",
        caption_kind=caption_kind,
        language=language,
        cookie_browser=cookie_browser,
    )


def acquire_bilibili_captions(
    source: str,
    output_dir: Path,
) -> dict[str, Any]:
    ytdlp = command_path("yt-dlp", "JAY_CONTEXT_YTDLP_BIN")
    cookie_browser = youtube_cookie_browser()
    info: dict[str, Any] = {}
    info_process = run(
        [
            ytdlp,
            "--cookies-from-browser",
            cookie_browser,
            "--no-playlist",
            "--skip-download",
            "--ignore-no-formats-error",
            "--dump-single-json",
            "--no-warnings",
            source,
        ]
    )
    if info_process.returncode == 0:
        try:
            parsed_info = json.loads(info_process.stdout)
            if isinstance(parsed_info, dict):
                info = parsed_info
        except json.JSONDecodeError:
            pass
    language = "ai-zh"
    output_template = str(output_dir / "source-captions.%(ext)s")
    caption_process = run(
        [
            ytdlp,
            "--cookies-from-browser",
            cookie_browser,
            "--no-playlist",
            "--skip-download",
            "--no-warnings",
            "--write-subs",
            "--sub-langs",
            language,
            "--sub-format",
            "srt",
            "--no-overwrites",
            "-o",
            output_template,
            source,
        ]
    )
    if caption_process.returncode != 0:
        detail = (caption_process.stderr or caption_process.stdout).strip()[-1200:]
        raise RuntimeError(
            f"Cookie-authenticated Bilibili caption download failed: {detail}"
        )
    try:
        caption_path = find_caption_file(output_dir, language)
    except RuntimeError as exc:
        detail = (caption_process.stderr or caption_process.stdout).strip()[-1200:]
        raise RuntimeError(
            "Cookie-authenticated Bilibili ai-zh captions are unavailable"
            + (f": {detail}" if detail else ".")
        ) from exc
    return persist_platform_captions(
        source=source,
        output_dir=output_dir,
        caption_path=caption_path,
        info=info,
        platform="bilibili",
        caption_kind="ai-generated",
        language=language,
        cookie_browser=cookie_browser,
    )


def download_direct_media(
    media_url: str,
    output_dir: Path,
    source_url: str,
    title: str | None,
    acquisition: str,
) -> tuple[Path, str | None]:
    request = urllib.request.Request(media_url, headers={"User-Agent": UA})
    try:
        with urllib.request.urlopen(request, timeout=60.0) as response:
            headers = dict(response.headers)
            final_url = response.geturl()
            extension = extension_for_url(final_url, headers)
            destination = output_dir / f"source-media{extension}"
            partial = destination.with_suffix(destination.suffix + ".part")
            if not destination.exists():
                with partial.open("wb") as handle:
                    shutil.copyfileobj(response, handle)
                partial.replace(destination)
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(
            f"HTTP {exc.code} while downloading {media_url}: {body[:500]}"
        ) from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(
            f"Media download failed for {media_url}: {exc.reason}"
        ) from exc
    if not destination.is_file() or destination.stat().st_size == 0:
        raise RuntimeError("Media download completed without a usable local file.")
    write_info_json(
        output_dir,
        {
            "title": title or destination.stem,
            "source_url": source_url,
            "resolved_media_url": media_url,
            "acquisition": acquisition,
        },
    )
    return destination.resolve(), title


def acquire_with_ytdlp(
    source: str,
    output_dir: Path,
) -> tuple[Path, str | None]:
    ytdlp = command_path("yt-dlp", "JAY_CONTEXT_YTDLP_BIN")
    output_template = str(output_dir / "source-media.%(ext)s")
    base = [
        ytdlp,
        "--no-playlist",
        "-f",
        "bestaudio",
        "--write-info-json",
        "--no-write-playlist-metafiles",
        "--no-overwrites",
        "-o",
        output_template,
        source,
    ]
    attempts = [
        [
            ytdlp,
            "--cookies-from-browser",
            youtube_cookie_browser(),
            *base[1:],
        ],
        base,
    ]
    errors: list[str] = []
    for command in attempts:
        process = run(command)
        if process.returncode == 0:
            break
        errors.append((process.stderr or process.stdout).strip()[-800:])
    else:
        raise RuntimeError("yt-dlp failed: " + " | ".join(errors))

    candidates = [
        path
        for path in output_dir.glob("source-media.*")
        if path.suffix not in {".json", ".part", ".ytdl"}
    ]
    if not candidates:
        raise RuntimeError("yt-dlp completed without a downloaded media file.")
    media_path = max(candidates, key=lambda path: path.stat().st_size)
    title = None
    info_path = output_dir / "source-media.info.json"
    if info_path.exists():
        try:
            title = json.loads(info_path.read_text(encoding="utf-8")).get("title")
        except (json.JSONDecodeError, OSError):
            title = None
    return media_path.resolve(), title


def acquire_url_media(source: str, output_dir: Path) -> tuple[Path, str | None]:
    errors: list[str] = []
    if is_direct_media_url(source):
        try:
            return download_direct_media(
                source,
                output_dir,
                source,
                Path(urllib.parse.urlparse(source).path).stem or None,
                "direct-media-download",
            )
        except RuntimeError as exc:
            errors.append(str(exc))

    try:
        return acquire_with_ytdlp(source, output_dir)
    except RuntimeError as exc:
        errors.append(str(exc))

    try:
        resolved = resolve_page_media(source)
        return download_direct_media(
            resolved["media_url"],
            output_dir,
            source,
            resolved.get("title"),
            resolved.get("acquisition") or "resolved-media-download",
        )
    except (RuntimeError, ET.ParseError, json.JSONDecodeError) as exc:
        errors.append(str(exc))

    raise RuntimeError("Local media acquisition failed: " + " | ".join(errors))


def doubao_command(args: argparse.Namespace, source: str) -> list[str]:
    command = [
        sys.executable,
        str(DOUBAO_SCRIPT),
        source,
        "--output-dir",
        args.output_dir,
        "--http-timeout",
        str(args.http_timeout),
    ]
    append_option(command, "--title", args.title)
    append_option(command, "--api-key-file", args.api_key_file)
    append_option(command, "--local-resource-id", args.local_resource_id)
    if args.speaker_info:
        command.append("--speaker-info")
    if args.no_punc:
        command.append("--no-punc")
    if args.plain_text:
        command.append("--plain-text")
    if args.dry_run:
        command.append("--dry-run")
    return command


def report_success(
    payload: dict[str, Any],
    args: argparse.Namespace,
    acquired_media: Path | None,
    extra: dict[str, Any] | None = None,
) -> None:
    payload["engine"] = "doubao-flash-asr"
    payload["fallback_used"] = False
    payload["doubao_attempted"] = True
    payload["source_url"] = args.source if is_url(args.source) else None
    if acquired_media:
        payload["local_media_path"] = str(acquired_media)
    if extra:
        payload.update(extra)
    print(json.dumps(payload, ensure_ascii=False, indent=2))


def report_failure(
    stage: str,
    payload: dict[str, Any] | None,
    extra: dict[str, Any] | None = None,
    returncode: int = 1,
) -> None:
    message = (
        "Local media acquisition failed; Doubao Flash was not attempted."
        if stage == "media-download"
        else "Doubao Flash transcription failed; no fallback is available."
    )
    error = {
        "ok": False,
        "error": message,
        "stage": stage,
        "doubao_attempted": stage != "media-download",
        "doubao_error": (payload or {}).get("error"),
    }
    if extra:
        error.update(extra)
    print(json.dumps(error, ensure_ascii=False), file=sys.stderr)
    sys.exit(returncode or 1)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Download media locally and transcribe with Doubao Flash."
    )
    parser.add_argument("source")
    parser.add_argument("--output-dir", default=".")
    parser.add_argument("--title")
    parser.add_argument("--api-key-file")
    parser.add_argument("--local-resource-id")
    parser.add_argument("--speaker-info", action="store_true")
    parser.add_argument("--no-punc", action="store_true")
    parser.add_argument("--plain-text", action="store_true")
    parser.add_argument("--http-timeout", type=float, default=600.0)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    output_dir = Path(args.output_dir).expanduser().resolve()
    local_source = Path(args.source).expanduser()
    source_is_local = local_source.is_file()
    source_is_url = is_url(args.source)
    if not source_is_local and not source_is_url:
        parser.error("source must be an existing local file or an HTTP(S) URL")

    if args.dry_run and source_is_url:
        caption_platform = (
            "youtube"
            if is_youtube_url(args.source)
            else "bilibili"
            if is_bilibili_url(args.source)
            else None
        )
        print(
            json.dumps(
                {
                    "ok": True,
                    "dry_run": True,
                    "route": (
                        f"{caption_platform}-browser-cookie-captions-then-audio-doubao-flash"
                        if caption_platform
                        else "download-local-then-doubao-flash"
                    ),
                    "source": args.source,
                    "acquisition": (
                        f"{caption_platform}-captions-with-browser-cookies"
                        if caption_platform
                        else "yt-dlp-audio-download"
                        if is_platform_page(args.source)
                        else "direct-or-resolved-media-download"
                    ),
                    "platform_captions": (
                        {
                            "planned": True,
                            "platform": caption_platform,
                            "language": (
                                "ai-zh"
                                if caption_platform == "bilibili"
                                else "best-available"
                            ),
                            "browser_cookie_source": youtube_cookie_browser(),
                        }
                        if caption_platform
                        else None
                    ),
                    "doubao": {
                        "eligible": True,
                        "mode": "local-base64-flash-after-download",
                        "fallback_only": bool(caption_platform),
                    },
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        return

    output_dir.mkdir(parents=True, exist_ok=True)
    acquired_media: Path | None = None
    caption_platform: str | None = None
    platform_caption_error: str | None = None
    execution_source = str(local_source.resolve()) if source_is_local else ""
    if source_is_url:
        if is_youtube_url(args.source):
            caption_platform = "youtube"
            caption_acquirer = acquire_youtube_captions
        elif is_bilibili_url(args.source):
            caption_platform = "bilibili"
            caption_acquirer = acquire_bilibili_captions
        else:
            caption_acquirer = None
        if caption_acquirer:
            try:
                print(
                    json.dumps(
                        caption_acquirer(args.source, output_dir),
                        ensure_ascii=False,
                        indent=2,
                    )
                )
                return
            except RuntimeError as exc:
                platform_caption_error = str(exc)
        try:
            acquired_media, resolved_title = acquire_url_media(args.source, output_dir)
        except RuntimeError as exc:
            extra = {"acquisition_error": str(exc)}
            if caption_platform and platform_caption_error:
                extra.update(
                    {
                        "platform_captions_attempted": True,
                        "platform_caption_error": platform_caption_error,
                        f"{caption_platform}_captions_attempted": True,
                        f"{caption_platform}_caption_error": platform_caption_error,
                        "doubao_attempted": False,
                    }
                )
            report_failure("media-download", None, extra)
        execution_source = str(acquired_media)
        if not args.title and resolved_title:
            args.title = resolved_title

    primary = run(doubao_command(args, execution_source))
    primary_payload = parse_payload(primary)
    if primary.returncode == 0:
        extra = None
        if caption_platform and platform_caption_error:
            extra = {
                "platform_captions_attempted": True,
                "platform_caption_error": platform_caption_error,
                "platform_audio_fallback_used": True,
                f"{caption_platform}_captions_attempted": True,
                f"{caption_platform}_caption_error": platform_caption_error,
                f"{caption_platform}_audio_fallback_used": True,
            }
        report_success(primary_payload, args, acquired_media, extra)
        return
    extra = {"local_media_path": execution_source}
    if caption_platform and platform_caption_error:
        extra.update(
            {
                "platform_captions_attempted": True,
                "platform_caption_error": platform_caption_error,
                "platform_audio_fallback_used": True,
                f"{caption_platform}_captions_attempted": True,
                f"{caption_platform}_caption_error": platform_caption_error,
                f"{caption_platform}_audio_fallback_used": True,
            }
        )
    report_failure(
        "doubao-local-base64",
        primary_payload,
        extra,
        primary.returncode,
    )


if __name__ == "__main__":
    main()
