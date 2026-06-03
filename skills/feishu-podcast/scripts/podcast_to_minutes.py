#!/usr/bin/env python3
import argparse
import html
import json
import os
import re
import subprocess
import sys
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path


UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X) feishu-podcast/1.0"


def request(url, data=None, headers=None, timeout=30):
    body = None
    req_headers = {"User-Agent": UA}
    if headers:
        req_headers.update(headers)
    if data is not None:
        body = json.dumps(data).encode("utf-8")
        req_headers["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=body, headers=req_headers)
    with urllib.request.urlopen(req, timeout=timeout) as res:
        return res.read(), dict(res.headers), res.geturl()


def decode_text(raw, headers):
    content_type = headers.get("Content-Type", "")
    match = re.search(r"charset=([^;\s]+)", content_type, re.I)
    encoding = match.group(1) if match else "utf-8"
    return raw.decode(encoding, errors="replace")


def slugify(text, fallback="podcast-episode"):
    text = html.unescape(text or "").strip()
    text = re.sub(r"[^\w\s.,'&()+-]+", "", text, flags=re.UNICODE)
    text = re.sub(r"\s+", " ", text).strip()
    if not text:
        text = fallback
    text = text[:100].strip(" .")
    return text.replace("/", "-") + ".mp3"


def simplecast_lookup(url):
    host = urllib.parse.urlparse(url).netloc.lower()
    if "simplecast.com" not in host:
        return None
    raw, _, _ = request(
        "https://api.simplecast.com/episodes/search",
        data={"url": url},
        headers={"Accept": "application/json"},
    )
    episode = json.loads(raw.decode("utf-8"))
    audio_url = episode.get("enclosure_url")
    if audio_url:
        return {
            "audio_url": audio_url,
            "title": episode.get("title") or "podcast episode",
            "source": "simplecast-api",
        }
    return None


def parse_rss(raw, page_url):
    root = ET.fromstring(raw)
    channel_title = root.findtext("./channel/title") or "podcast"
    first_item = root.find("./channel/item")
    if first_item is None:
        return None
    item_title = first_item.findtext("title") or channel_title
    enclosure = first_item.find("enclosure")
    if enclosure is not None and enclosure.attrib.get("url"):
        return {
            "audio_url": urllib.parse.urljoin(page_url, enclosure.attrib["url"]),
            "title": item_title,
            "source": "rss-enclosure",
        }
    return None


def find_html_audio(raw, page_url):
    text = decode_text(raw, {"Content-Type": "text/html"})
    unescaped = html.unescape(text)

    mp3_match = re.search(r"https?://[^\"'<>\s]+\.mp3(?:\?[^\"'<>\s]*)?", unescaped, re.I)
    if mp3_match:
        title = find_html_title(unescaped) or "podcast episode"
        return {"audio_url": mp3_match.group(0), "title": title, "source": "html-mp3"}

    rss_match = re.search(
        r'<link[^>]+(?:type=["\']application/rss\+xml["\'][^>]+href=["\']([^"\']+)["\']|href=["\']([^"\']+)["\'][^>]+type=["\']application/rss\+xml["\'])',
        unescaped,
        re.I,
    )
    if rss_match:
        rss_url = urllib.parse.urljoin(page_url, rss_match.group(1) or rss_match.group(2))
        raw_rss, _, final_url = request(rss_url)
        return parse_rss(raw_rss, final_url)
    return None


def find_html_title(text):
    og = re.search(r'<meta[^>]+property=["\']og:title["\'][^>]+content=["\']([^"\']+)["\']', text, re.I)
    if og:
        return og.group(1)
    title = re.search(r"<title[^>]*>(.*?)</title>", text, re.I | re.S)
    if title:
        return re.sub(r"\s+", " ", title.group(1)).strip()
    return None


def resolve_audio(url):
    parsed = urllib.parse.urlparse(url)
    if parsed.path.lower().endswith(".mp3"):
        return {"audio_url": url, "title": Path(parsed.path).stem, "source": "direct-mp3"}

    simplecast = simplecast_lookup(url)
    if simplecast:
        return simplecast

    raw, headers, final_url = request(url)
    content_type = headers.get("Content-Type", "").lower()
    if "xml" in content_type or raw.lstrip().startswith(b"<?xml"):
        rss = parse_rss(raw, final_url)
        if rss:
            return rss
    html_audio = find_html_audio(raw, final_url)
    if html_audio:
        return html_audio
    raise RuntimeError("Could not resolve an MP3 URL from the podcast page.")


def download(url, output_path):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=60) as res, open(output_path, "wb") as out:
        while True:
            chunk = res.read(1024 * 1024)
            if not chunk:
                break
            out.write(chunk)


def extract_json_object(text):
    candidates = []
    for match in re.finditer(r"{", text):
        start = match.start()
        depth = 0
        in_str = False
        escape = False
        for i in range(start, len(text)):
            ch = text[i]
            if in_str:
                if escape:
                    escape = False
                elif ch == "\\":
                    escape = True
                elif ch == '"':
                    in_str = False
            else:
                if ch == '"':
                    in_str = True
                elif ch == "{":
                    depth += 1
                elif ch == "}":
                    depth -= 1
                    if depth == 0:
                        candidates.append(text[start : i + 1])
                        break
    for candidate in reversed(candidates):
        try:
            return json.loads(candidate)
        except json.JSONDecodeError:
            continue
    raise RuntimeError("No JSON object found in lark-cli output.")


def run_lark(args):
    proc = subprocess.run(["lark-cli", *args], text=True, capture_output=True)
    combined = (proc.stdout or "") + "\n" + (proc.stderr or "")
    if proc.returncode != 0:
        raise RuntimeError(combined.strip())
    return extract_json_object(combined)


def upload_to_minutes(mp3_path):
    uploaded = run_lark(["drive", "+upload", "--file", str(mp3_path), "--name", mp3_path.name])
    data = uploaded.get("data") or {}
    file_token = data.get("file_token")
    if not file_token:
        raise RuntimeError("drive +upload did not return data.file_token")
    minute = run_lark(["minutes", "+upload", "--file-token", file_token])
    minute_data = minute.get("data") or {}
    return {
        "file_token": file_token,
        "drive_url": data.get("url"),
        "minute_url": minute_data.get("minute_url"),
    }


def main():
    parser = argparse.ArgumentParser(description="Download a podcast MP3 and create Feishu Minutes.")
    parser.add_argument("url", help="Podcast episode URL, RSS URL, or direct MP3 URL")
    parser.add_argument("--output-dir", default=".", help="Directory for the downloaded MP3")
    parser.add_argument("--filename", help="Override downloaded MP3 filename")
    parser.add_argument("--download-only", action="store_true", help="Only download the MP3; do not upload to Feishu")
    args = parser.parse_args()

    resolved = resolve_audio(args.url)
    output_dir = Path(args.output_dir).expanduser().resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    filename = args.filename or slugify(resolved.get("title"))
    if not filename.lower().endswith(".mp3"):
        filename += ".mp3"
    mp3_path = output_dir / filename

    download(resolved["audio_url"], mp3_path)
    result = {
        "ok": True,
        "source": resolved.get("source"),
        "title": resolved.get("title"),
        "audio_url": resolved["audio_url"],
        "mp3_path": str(mp3_path),
        "size_bytes": mp3_path.stat().st_size,
    }
    if not args.download_only:
        result.update(upload_to_minutes(mp3_path))
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    try:
        main()
    except (urllib.error.URLError, RuntimeError, ET.ParseError, subprocess.SubprocessError) as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False, indent=2), file=sys.stderr)
        sys.exit(1)
