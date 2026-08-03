#!/usr/bin/env python3
"""Transcribe local media with Doubao Flash ASR."""

from __future__ import annotations

import argparse
import base64
import json
import math
import os
import re
import shutil
import subprocess
import sys
import urllib.error
import urllib.request
import uuid
from pathlib import Path
from typing import Any


FLASH_URL = "https://openspeech.bytedance.com/api/v3/auc/bigmodel/recognize/flash"
DEFAULT_LOCAL_RESOURCE_ID = "volc.bigasr.auc_turbo"
COMPRESSION_TRIGGER_BYTES = 20 * 1024 * 1024
MAX_FLASH_BYTES = 100 * 1024 * 1024
MAX_FLASH_DURATION_MS = 2 * 60 * 60 * 1000
SEGMENT_DURATION_MS = 110 * 60 * 1000
FLASH_AUDIO_SUFFIXES = {".mp3", ".ogg", ".opus", ".wav"}
KEYCHAIN_ACCOUNT = "jay-context"
KEYCHAIN_SERVICE = "DOUBAO_ASR_API_KEY"
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X) jay-context/1.0"
SUCCESS_CODE = "20000000"


class AsrError(RuntimeError):
    """A recoverable, user-facing ASR workflow error."""


def header_value(headers: dict[str, str], name: str) -> str:
    wanted = name.lower()
    for key, value in headers.items():
        if key.lower() == wanted:
            return value
    return ""


def http_request(
    url: str,
    payload: dict[str, Any],
    headers: dict[str, str],
    timeout: float,
) -> tuple[bytes, dict[str, str]]:
    data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    request_headers = {
        "User-Agent": UA,
        "Content-Type": "application/json",
        **headers,
    }
    request = urllib.request.Request(url, data=data, headers=request_headers)
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return response.read(), dict(response.headers)
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise AsrError(f"HTTP {exc.code} from {url}: {body[:500]}") from exc
    except urllib.error.URLError as exc:
        raise AsrError(f"Request failed for {url}: {exc.reason}") from exc


def parse_json_body(raw: bytes) -> dict[str, Any]:
    if not raw.strip():
        return {}
    try:
        value = json.loads(raw.decode("utf-8"))
    except json.JSONDecodeError as exc:
        raise AsrError(f"ASR returned invalid JSON: {raw[:500]!r}") from exc
    if not isinstance(value, dict):
        raise AsrError("ASR returned a non-object JSON response.")
    return value


def api_headers(api_key: str, resource_id: str, request_id: str) -> dict[str, str]:
    return {
        "X-Api-Key": api_key,
        "X-Api-Resource-Id": resource_id,
        "X-Api-Request-Id": request_id,
        "X-Api-Sequence": "-1",
    }


def recognize_flash(
    api_key: str,
    resource_id: str,
    request_id: str,
    payload: dict[str, Any],
    timeout: float,
) -> tuple[dict[str, Any], dict[str, str]]:
    raw, headers = http_request(
        FLASH_URL,
        payload,
        api_headers(api_key, resource_id, request_id),
        timeout,
    )
    code = header_value(headers, "X-Api-Status-Code")
    if code != SUCCESS_CODE:
        message = header_value(headers, "X-Api-Message") or "unknown error"
        log_id = header_value(headers, "X-Tt-Logid") or "unavailable"
        raise AsrError(
            f"recognize-flash failed: status={code or 'missing'},message={message},"
            f"request_id={request_id},logid={log_id}"
        )
    response = parse_json_body(raw)
    if not response.get("result"):
        log_id = header_value(headers, "X-Tt-Logid") or "unavailable"
        raise AsrError(
            f"ASR completed without a result: request_id={request_id},logid={log_id}"
        )
    return response, headers


def command_path(name: str, env_name: str | None = None) -> str:
    if env_name:
        configured = os.environ.get(env_name, "").strip()
        if configured:
            path = Path(configured).expanduser()
            if path.exists():
                return str(path)
            raise AsrError(f"{env_name} points to a missing executable: {path}")
    found = shutil.which(name)
    if not found:
        raise AsrError(f"Required command is unavailable: {name}")
    return found


def run_media_command(command: list[str], stage: str) -> None:
    process = subprocess.run(command, text=True, capture_output=True)
    if process.returncode != 0:
        detail = (process.stderr or process.stdout).strip()
        raise AsrError(f"{stage} failed: {detail[-1200:]}")


def probe_duration_ms(source: Path) -> int:
    ffprobe = command_path("ffprobe", "JAY_CONTEXT_FFPROBE_BIN")
    process = subprocess.run(
        [
            ffprobe,
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "default=noprint_wrappers=1:nokey=1",
            str(source),
        ],
        text=True,
        capture_output=True,
    )
    if process.returncode != 0:
        detail = (process.stderr or process.stdout).strip()
        raise AsrError(f"ffprobe duration check failed: {detail[-1200:]}")
    try:
        duration_ms = int(round(float(process.stdout.strip()) * 1000))
    except ValueError as exc:
        raise AsrError(
            f"ffprobe returned an invalid duration for {source}: {process.stdout!r}"
        ) from exc
    if duration_ms <= 0:
        raise AsrError(f"Media duration must be positive: {source}")
    return duration_ms


def should_normalize(source: Path, duration_ms: int) -> bool:
    return (
        source.suffix.lower() not in FLASH_AUDIO_SUFFIXES
        or source.stat().st_size >= COMPRESSION_TRIGGER_BYTES
        or duration_ms > MAX_FLASH_DURATION_MS
    )


def planned_segment_count(duration_ms: int) -> int:
    if duration_ms <= MAX_FLASH_DURATION_MS:
        return 1
    return max(1, math.ceil(duration_ms / SEGMENT_DURATION_MS))


def validate_flash_file(path: Path, duration_ms: int) -> None:
    if not path.is_file() or path.stat().st_size == 0:
        raise AsrError(f"Prepared local audio is missing or empty: {path}")
    if path.stat().st_size > MAX_FLASH_BYTES:
        raise AsrError(
            "Prepared local audio exceeds Doubao Flash's 100MB limit: "
            f"{path.stat().st_size} bytes"
        )
    if duration_ms > MAX_FLASH_DURATION_MS:
        raise AsrError(
            "Prepared local audio exceeds Doubao Flash's 2-hour limit: "
            f"{duration_ms} milliseconds"
        )


def prepare_flash_segments(
    source: Path,
    work_dir: Path,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    source_duration_ms = probe_duration_ms(source)
    normalize = should_normalize(source, source_duration_ms)
    segmented = source_duration_ms > MAX_FLASH_DURATION_MS
    work_dir.mkdir(parents=True, exist_ok=False)

    if not normalize:
        validate_flash_file(source, source_duration_ms)
        return (
            [
                {
                    "index": 1,
                    "path": source,
                    "start_time": 0,
                    "duration": source_duration_ms,
                }
            ],
            {
                "source_bytes": source.stat().st_size,
                "source_duration_ms": source_duration_ms,
                "compression_trigger_bytes": COMPRESSION_TRIGGER_BYTES,
                "normalized": False,
                "segmented": False,
            },
        )

    ffmpeg = command_path("ffmpeg", "JAY_CONTEXT_FFMPEG_BIN")
    common = [
        ffmpeg,
        "-y",
        "-nostdin",
        "-hide_banner",
        "-loglevel",
        "error",
        "-i",
        str(source),
        "-vn",
        "-ac",
        "1",
        "-ar",
        "16000",
        "-c:a",
        "libmp3lame",
        "-b:a",
        "64k",
    ]
    if segmented:
        output_pattern = work_dir / "doubao-part-%03d.mp3"
        run_media_command(
            [
                *common,
                "-f",
                "segment",
                "-segment_time",
                str(SEGMENT_DURATION_MS / 1000),
                "-reset_timestamps",
                "1",
                str(output_pattern),
            ],
            "ffmpeg segmentation",
        )
        prepared_paths = sorted(work_dir.glob("doubao-part-*.mp3"))
    else:
        prepared = work_dir / "doubao-input.mp3"
        run_media_command([*common, str(prepared)], "ffmpeg audio preparation")
        prepared_paths = [prepared]

    if not prepared_paths:
        raise AsrError("ffmpeg preparation produced no audio segments.")

    segments: list[dict[str, Any]] = []
    start_time_ms = 0
    for index, path in enumerate(prepared_paths, start=1):
        duration_ms = probe_duration_ms(path)
        validate_flash_file(path, duration_ms)
        segments.append(
            {
                "index": index,
                "path": path,
                "start_time": start_time_ms,
                "duration": duration_ms,
            }
        )
        start_time_ms += duration_ms

    return (
        segments,
        {
            "source_bytes": source.stat().st_size,
            "source_duration_ms": source_duration_ms,
            "compression_trigger_bytes": COMPRESSION_TRIGGER_BYTES,
            "normalized": True,
            "segmented": segmented,
        },
    )


def request_payload(
    path: Path,
    uid: str,
    audio_format: str | None,
    speaker_info: bool,
    no_punc: bool,
) -> dict[str, Any]:
    return {
        "user": {"uid": uid},
        "audio": {
            "data": base64.b64encode(path.read_bytes()).decode("ascii"),
            "format": audio_format or path.suffix.lstrip(".") or "mp3",
            "codec": "raw",
            "rate": 16000,
            "bits": 16,
            "channel": 1,
        },
        "request": {
            "model_name": "bigmodel",
            "enable_itn": True,
            "enable_punc": not no_punc,
            "enable_ddc": False,
            "enable_speaker_info": speaker_info,
            "enable_channel_split": False,
            "show_utterances": True,
            "vad_segment": False,
            "sensitive_words_filter": "",
        },
    }


def add_timestamp_offset(value: Any, offset_ms: int) -> Any:
    try:
        return int(value) + offset_ms
    except (TypeError, ValueError):
        return value


def offset_utterance(utterance: dict[str, Any], offset_ms: int) -> dict[str, Any]:
    adjusted = dict(utterance)
    for key in ("start_time", "end_time"):
        if key in adjusted:
            adjusted[key] = add_timestamp_offset(adjusted[key], offset_ms)
    words = adjusted.get("words")
    if isinstance(words, list):
        adjusted_words: list[Any] = []
        for word in words:
            if not isinstance(word, dict):
                adjusted_words.append(word)
                continue
            adjusted_word = dict(word)
            for key in ("start_time", "end_time"):
                if key in adjusted_word:
                    adjusted_word[key] = add_timestamp_offset(
                        adjusted_word[key], offset_ms
                    )
            adjusted_words.append(adjusted_word)
        adjusted["words"] = adjusted_words
    return adjusted


def merge_segment_responses(
    completed: list[dict[str, Any]],
    total_duration_ms: int,
) -> dict[str, Any]:
    merged_texts: list[str] = []
    merged_utterances: list[dict[str, Any]] = []
    segment_records: list[dict[str, Any]] = []
    for item in completed:
        response = item["response"]
        result = response.get("result") or {}
        text = str(result.get("text") or "").strip()
        if text:
            merged_texts.append(text)
        utterances = result.get("utterances") or []
        for utterance in utterances:
            if isinstance(utterance, dict):
                merged_utterances.append(
                    offset_utterance(utterance, item["start_time"])
                )
        segment_records.append(
            {
                "index": item["index"],
                "start_time": item["start_time"],
                "duration": item["duration"],
                "request_id": item["request_id"],
                "log_id": item["log_id"],
                "response": response,
            }
        )
    return {
        "audio_info": {"duration": total_duration_ms},
        "result": {
            "text": "\n".join(merged_texts),
            "utterances": merged_utterances,
        },
        "segments": segment_records,
    }


def timestamp(milliseconds: Any) -> str:
    try:
        total = max(0, int(milliseconds)) // 1000
    except (TypeError, ValueError):
        total = 0
    hours, remainder = divmod(total, 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}"


def transcript_text(response: dict[str, Any], plain_text: bool) -> str:
    result = response.get("result") or {}
    utterances = result.get("utterances") or []
    lines: list[str] = []
    for utterance in utterances:
        text = str(utterance.get("text") or "").strip()
        if not text:
            continue
        speaker = (
            utterance.get("speaker_id")
            or utterance.get("speaker")
            or utterance.get("speaker_tag")
        )
        if plain_text:
            prefix = f"Speaker {speaker}: " if speaker is not None else ""
        else:
            prefix = f"[{timestamp(utterance.get('start_time'))}] "
            if speaker is not None:
                prefix += f"Speaker {speaker}: "
        lines.append(prefix + text)
    if lines:
        return "\n".join(lines).strip() + "\n"
    text = str(result.get("text") or "").strip()
    if not text:
        raise AsrError("ASR completed without result.text or result.utterances.")
    return text + "\n"


def slugify(text: str | None, fallback: str = "media") -> str:
    value = (text or "").strip()
    value = re.sub(r"[^\w\s.,'&()+-]+", "", value, flags=re.UNICODE)
    value = re.sub(r"\s+", "-", value).strip("-_.")
    return (value or fallback)[:100]


def read_keychain_api_key() -> str:
    try:
        process = subprocess.run(
            [
                "security",
                "find-generic-password",
                "-a",
                KEYCHAIN_ACCOUNT,
                "-s",
                KEYCHAIN_SERVICE,
                "-w",
            ],
            text=True,
            capture_output=True,
        )
    except FileNotFoundError:
        return ""
    return process.stdout.strip() if process.returncode == 0 else ""


def read_api_key(key_file: str | None) -> str:
    if key_file:
        value = Path(key_file).expanduser().read_text(encoding="utf-8").strip()
    else:
        value = os.environ.get("DOUBAO_ASR_API_KEY", "").strip()
        if not value:
            value = read_keychain_api_key()
    if not value:
        raise AsrError(
            "Store DOUBAO_ASR_API_KEY in macOS Keychain,set the environment variable,"
            "or pass --api-key-file before sending an ASR request."
        )
    return value


def write_json(path: Path, value: dict[str, Any]) -> None:
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def failure_manifest(
    source: Path,
    work_dir: Path,
    preprocessing: dict[str, Any],
    completed: list[dict[str, Any]],
    failed_segment: dict[str, Any],
    error: str,
) -> dict[str, Any]:
    return {
        "ok": False,
        "mode": (
            "local-base64-flash-segmented"
            if preprocessing.get("segmented")
            else "local-base64-flash"
        ),
        "source": str(source),
        "work_dir": str(work_dir),
        "preprocessing": preprocessing,
        "completed_segments": [
            {
                "index": item["index"],
                "start_time": item["start_time"],
                "duration": item["duration"],
                "request_id": item["request_id"],
                "log_id": item["log_id"],
            }
            for item in completed
        ],
        "failed_segment": {
            "index": failed_segment["index"],
            "path": str(failed_segment["path"]),
            "start_time": failed_segment["start_time"],
            "duration": failed_segment["duration"],
        },
        "error": error,
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Transcribe a local media file with Doubao Flash ASR."
    )
    parser.add_argument("source", help="Existing local audio or video file")
    parser.add_argument("--output-dir", default=".", help="Directory for ASR artifacts")
    parser.add_argument("--title", help="Override artifact title")
    parser.add_argument("--format", dest="audio_format", help="Override ASR audio format")
    parser.add_argument("--uid", default="jay-context", help="Non-sensitive ASR user identifier")
    parser.add_argument(
        "--local-resource-id",
        default=os.environ.get(
            "JAY_CONTEXT_DOUBAO_LOCAL_RESOURCE_ID", DEFAULT_LOCAL_RESOURCE_ID
        ),
        help="Resource ID for Doubao Flash local-file recognition",
    )
    parser.add_argument("--api-key-file", help="Read API key from a local file")
    parser.add_argument("--http-timeout", type=float, default=600.0)
    parser.add_argument("--speaker-info", action="store_true")
    parser.add_argument("--no-punc", action="store_true")
    parser.add_argument("--plain-text", action="store_true")
    parser.add_argument("--dry-run", action="store_true", help="Print the local Flash plan")
    args = parser.parse_args()

    source = Path(args.source).expanduser().resolve()
    if not source.is_file():
        raise AsrError(f"Source must be an existing local media file: {source}")

    title = args.title or source.stem
    slug = slugify(title)
    output_dir = Path(args.output_dir).expanduser().resolve()
    json_path = output_dir / f"{slug}-asr.json"
    transcript_path = output_dir / f"{slug}-raw-transcript.txt"
    failure_path = output_dir / f"{slug}-asr-failure.json"
    source_duration_ms = probe_duration_ms(source)
    normalize = should_normalize(source, source_duration_ms)
    segment_count = planned_segment_count(source_duration_ms)

    if args.dry_run:
        print(
            json.dumps(
                {
                    "ok": True,
                    "dry_run": True,
                    "mode": (
                        "local-base64-flash-segmented"
                        if segment_count > 1
                        else "local-base64-flash"
                    ),
                    "resource_id": args.local_resource_id,
                    "local_media_path": str(source),
                    "source_bytes": source.stat().st_size,
                    "source_duration_ms": source_duration_ms,
                    "compression_trigger_bytes": COMPRESSION_TRIGGER_BYTES,
                    "will_normalize": normalize,
                    "planned_segments": segment_count,
                    "segment_duration_ms": SEGMENT_DURATION_MS,
                    "api_key_set": bool(
                        args.api_key_file
                        or os.environ.get("DOUBAO_ASR_API_KEY")
                        or read_keychain_api_key()
                    ),
                    "json_path": str(json_path),
                    "transcript_path": str(transcript_path),
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        return

    output_dir.mkdir(parents=True, exist_ok=True)
    api_key = read_api_key(args.api_key_file)
    run_id = str(uuid.uuid4())
    work_dir = output_dir / f".{slug}-flash-{run_id[:8]}"
    segments, preprocessing = prepare_flash_segments(source, work_dir)
    completed: list[dict[str, Any]] = []

    for segment in segments:
        request_id = str(uuid.uuid4())
        try:
            response, headers = recognize_flash(
                api_key,
                args.local_resource_id,
                request_id,
                request_payload(
                    segment["path"],
                    args.uid,
                    args.audio_format,
                    args.speaker_info,
                    args.no_punc,
                ),
                args.http_timeout,
            )
        except AsrError as exc:
            manifest = failure_manifest(
                source,
                work_dir,
                preprocessing,
                completed,
                segment,
                str(exc),
            )
            write_json(failure_path, manifest)
            raise AsrError(
                f"{exc}; failure_manifest={failure_path}; preserved_work_dir={work_dir}"
            ) from exc
        item = {
            **segment,
            "request_id": request_id,
            "log_id": header_value(headers, "X-Tt-Logid") or None,
            "response": response,
        }
        completed.append(item)
        write_json(
            work_dir / f"{slug}-part-{segment['index']:03d}-asr.json",
            response,
        )

    if len(completed) == 1:
        final_response = completed[0]["response"]
        mode = "local-base64-flash"
    else:
        final_response = merge_segment_responses(completed, source_duration_ms)
        mode = "local-base64-flash-segmented"

    text = transcript_text(final_response, args.plain_text)
    write_json(json_path, final_response)
    transcript_path.write_text(text, encoding="utf-8")
    if failure_path.exists():
        failure_path.unlink()
    shutil.rmtree(work_dir)

    print(
        json.dumps(
            {
                "ok": True,
                "request_id": (
                    completed[0]["request_id"] if len(completed) == 1 else None
                ),
                "request_ids": [item["request_id"] for item in completed],
                "log_id": completed[0]["log_id"] if len(completed) == 1 else None,
                "log_ids": [item["log_id"] for item in completed],
                "mode": mode,
                "resource_id": args.local_resource_id,
                "source": "local-file-data",
                "local_media_path": str(source),
                "title": title,
                "preprocessing": preprocessing,
                "segments": len(completed),
                "json_path": str(json_path),
                "transcript_path": str(transcript_path),
                "characters": len(text),
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    try:
        main()
    except (AsrError, json.JSONDecodeError, OSError) as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        sys.exit(1)
