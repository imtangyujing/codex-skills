from __future__ import annotations

import argparse
import importlib.util
import io
import json
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from types import ModuleType
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]


def load_module(name: str, path: Path) -> ModuleType:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load module: {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


doubao = load_module("jay_context_doubao_asr", ROOT / "scripts" / "doubao_asr.py")
transcribe = load_module(
    "jay_context_transcribe_media", ROOT / "scripts" / "transcribe_media.py"
)


def response(text: str, start: int, end: int) -> dict:
    return {
        "audio_info": {"duration": end - start},
        "result": {
            "text": text,
            "utterances": [
                {
                    "start_time": start,
                    "end_time": end,
                    "text": text,
                    "speaker_id": 1,
                    "words": [
                        {
                            "start_time": start,
                            "end_time": end,
                            "text": text,
                        }
                    ],
                }
            ],
        },
    }


class ThresholdTests(unittest.TestCase):
    def test_compression_threshold_and_supported_format(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            below = root / "below.mp3"
            below.write_bytes(b"x")
            with mock.patch.object(
                Path, "stat", autospec=True
            ) as stat_mock:
                stat_mock.return_value.st_size = doubao.COMPRESSION_TRIGGER_BYTES - 1
                self.assertFalse(doubao.should_normalize(below, 60_000))
                stat_mock.return_value.st_size = doubao.COMPRESSION_TRIGGER_BYTES
                self.assertTrue(doubao.should_normalize(below, 60_000))
                stat_mock.return_value.st_size = doubao.COMPRESSION_TRIGGER_BYTES + 1
                self.assertTrue(doubao.should_normalize(below, 60_000))

    def test_video_container_always_normalizes(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            video = Path(temporary) / "source.mp4"
            video.write_bytes(b"x")
            self.assertTrue(doubao.should_normalize(video, 60_000))

    def test_segmentation_starts_only_after_two_hours(self) -> None:
        self.assertEqual(doubao.planned_segment_count(7_199_999), 1)
        self.assertEqual(doubao.planned_segment_count(7_200_000), 1)
        self.assertEqual(doubao.planned_segment_count(7_200_001), 2)
        self.assertEqual(
            doubao.planned_segment_count(3 * doubao.SEGMENT_DURATION_MS),
            3,
        )


class MergeTests(unittest.TestCase):
    def test_segment_merge_offsets_utterance_and_word_timestamps(self) -> None:
        completed = [
            {
                "index": 1,
                "start_time": 0,
                "duration": 6_600_000,
                "request_id": "req-1",
                "log_id": "log-1",
                "response": response("第一段", 100, 500),
            },
            {
                "index": 2,
                "start_time": 6_600_000,
                "duration": 600_000,
                "request_id": "req-2",
                "log_id": "log-2",
                "response": response("第二段", 200, 600),
            },
        ]
        merged = doubao.merge_segment_responses(completed, 7_200_000)
        self.assertEqual(merged["result"]["text"], "第一段\n第二段")
        second = merged["result"]["utterances"][1]
        self.assertEqual(second["start_time"], 6_600_200)
        self.assertEqual(second["end_time"], 6_600_600)
        self.assertEqual(second["words"][0]["start_time"], 6_600_200)
        self.assertEqual(merged["segments"][1]["request_id"], "req-2")
        self.assertEqual(merged["segments"][1]["response"]["result"]["text"], "第二段")


class PipelineTests(unittest.TestCase):
    def prepared_segments(
        self,
        source: Path,
        durations: list[int],
    ):
        def prepare(_source: Path, work_dir: Path):
            work_dir.mkdir(parents=True)
            segments = []
            start = 0
            for index, duration in enumerate(durations, start=1):
                path = work_dir / f"doubao-part-{index:03d}.mp3"
                path.write_bytes(b"audio")
                segments.append(
                    {
                        "index": index,
                        "path": path,
                        "start_time": start,
                        "duration": duration,
                    }
                )
                start += duration
            return (
                segments,
                {
                    "source_bytes": source.stat().st_size,
                    "source_duration_ms": sum(durations),
                    "compression_trigger_bytes": doubao.COMPRESSION_TRIGGER_BYTES,
                    "normalized": True,
                    "segmented": len(durations) > 1,
                },
            )

        return prepare

    def test_multi_segment_success_merges_and_cleans_work_files(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "source.mp3"
            source.write_bytes(b"source")
            output = root / "output"
            responses = [
                (response("第一段", 0, 1000), {"X-Tt-Logid": "log-1"}),
                (response("第二段", 0, 1000), {"X-Tt-Logid": "log-2"}),
            ]
            argv = [
                "doubao_asr.py",
                str(source),
                "--output-dir",
                str(output),
            ]
            with (
                mock.patch.object(sys, "argv", argv),
                mock.patch.object(doubao, "probe_duration_ms", return_value=7_300_000),
                mock.patch.object(
                    doubao,
                    "prepare_flash_segments",
                    side_effect=self.prepared_segments(
                        source, [6_600_000, 700_000]
                    ),
                ),
                mock.patch.object(doubao, "read_api_key", return_value="secret"),
                mock.patch.object(
                    doubao, "recognize_flash", side_effect=responses
                ),
                mock.patch.object(doubao, "request_payload", return_value={}),
                redirect_stdout(io.StringIO()),
            ):
                doubao.main()

            merged_path = output / "source-asr.json"
            transcript_path = output / "source-raw-transcript.txt"
            self.assertTrue(merged_path.is_file())
            self.assertTrue(transcript_path.is_file())
            merged = json.loads(merged_path.read_text(encoding="utf-8"))
            self.assertEqual(len(merged["segments"]), 2)
            self.assertEqual(
                merged["result"]["utterances"][1]["start_time"], 6_600_000
            )
            self.assertEqual(list(output.glob(".source-flash-*")), [])

    def test_segment_failure_keeps_work_files_and_blocks_final_output(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "source.mp3"
            source.write_bytes(b"source")
            output = root / "output"
            argv = [
                "doubao_asr.py",
                str(source),
                "--output-dir",
                str(output),
            ]
            side_effects = [
                (response("第一段", 0, 1000), {"X-Tt-Logid": "log-1"}),
                doubao.AsrError("second segment failed"),
            ]
            with (
                mock.patch.object(sys, "argv", argv),
                mock.patch.object(doubao, "probe_duration_ms", return_value=7_300_000),
                mock.patch.object(
                    doubao,
                    "prepare_flash_segments",
                    side_effect=self.prepared_segments(
                        source, [6_600_000, 700_000]
                    ),
                ),
                mock.patch.object(doubao, "read_api_key", return_value="secret"),
                mock.patch.object(
                    doubao, "recognize_flash", side_effect=side_effects
                ),
                mock.patch.object(doubao, "request_payload", return_value={}),
                redirect_stdout(io.StringIO()),
            ):
                with self.assertRaises(doubao.AsrError):
                    doubao.main()

            self.assertFalse((output / "source-asr.json").exists())
            self.assertFalse((output / "source-raw-transcript.txt").exists())
            failure_path = output / "source-asr-failure.json"
            self.assertTrue(failure_path.is_file())
            failure = json.loads(failure_path.read_text(encoding="utf-8"))
            self.assertEqual(len(failure["completed_segments"]), 1)
            self.assertTrue(Path(failure["work_dir"]).is_dir())
            self.assertTrue(
                list(Path(failure["work_dir"]).glob("*part-001-asr.json"))
            )


class AcquisitionTests(unittest.TestCase):
    def test_platform_router_only_marks_youtube_for_caption_lookup(self) -> None:
        self.assertTrue(
            transcribe.is_youtube_url("https://www.youtube.com/watch?v=abc")
        )
        self.assertTrue(transcribe.is_youtube_url("https://youtu.be/abc"))
        self.assertFalse(
            transcribe.is_youtube_url("https://www.bilibili.com/video/BV1abc")
        )
        self.assertTrue(
            transcribe.is_bilibili_url(
                "https://www.bilibili.com/video/BV1abc"
            )
        )
        self.assertTrue(transcribe.is_bilibili_url("https://b23.tv/example"))
        self.assertFalse(
            transcribe.is_youtube_url("https://vimeo.com/123")
        )

    def test_youtube_caption_lookup_and_download_use_browser_cookies(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary)
            info = {
                "id": "abc",
                "title": "Example",
                "language": "en",
                "subtitles": {},
                "automatic_captions": {
                    "en-orig": [{"ext": "json3"}],
                    "zh-Hans": [{"ext": "json3"}],
                },
            }
            commands: list[list[str]] = []

            def run_command(command: list[str]):
                commands.append(command)
                if "--dump-single-json" in command:
                    return subprocess_result(0, json.dumps(info), "")
                (output / "source-captions.en-orig.json3").write_text(
                    json.dumps(
                        {
                            "events": [
                                {
                                    "tStartMs": 1200,
                                    "segs": [{"utf8": "Hello world"}],
                                }
                            ]
                        }
                    ),
                    encoding="utf-8",
                )
                return subprocess_result(0, "", "")

            with mock.patch.object(transcribe, "run", side_effect=run_command):
                result = transcribe.acquire_youtube_captions(
                    "https://www.youtube.com/watch?v=abc",
                    output,
                )

            self.assertEqual(len(commands), 2)
            for command in commands:
                cookie_index = command.index("--cookies-from-browser")
                self.assertEqual(command[cookie_index + 1], "chrome")
                self.assertIn("--skip-download", command)
                self.assertNotIn("bestaudio", command)
            self.assertIn("--write-auto-subs", commands[1])
            self.assertEqual(result["caption_language"], "en-orig")
            self.assertFalse(result["doubao_attempted"])
            transcript = Path(result["transcript_path"]).read_text(encoding="utf-8")
            self.assertEqual(transcript, "[00:00:01] Hello world\n")

    def test_youtube_caption_success_skips_audio_and_doubao(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / "output"
            transcript = output / "source-captions-raw-transcript.txt"
            transcript.parent.mkdir(parents=True)
            transcript.write_text("caption", encoding="utf-8")
            caption_result = {
                "ok": True,
                "engine": "youtube-platform-captions",
                "transcript_path": str(transcript),
                "doubao_attempted": False,
            }
            argv = [
                "transcribe_media.py",
                "https://www.youtube.com/watch?v=abc",
                "--output-dir",
                str(output),
            ]
            with (
                mock.patch.object(sys, "argv", argv),
                mock.patch.object(
                    transcribe,
                    "acquire_youtube_captions",
                    return_value=caption_result,
                ) as captions,
                mock.patch.object(transcribe, "acquire_url_media") as audio,
                mock.patch.object(transcribe, "run") as run_command,
                redirect_stdout(io.StringIO()),
            ):
                transcribe.main()

            captions.assert_called_once()
            audio.assert_not_called()
            run_command.assert_not_called()

    def test_bilibili_caption_download_uses_cookies_and_ai_zh(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary)
            info = {
                "id": "BV1abc",
                "title": "Bilibili Example",
                "subtitles": {},
                "automatic_captions": {},
            }
            commands: list[list[str]] = []

            def run_command(command: list[str]):
                commands.append(command)
                if "--dump-single-json" in command:
                    return subprocess_result(0, json.dumps(info), "")
                (output / "source-captions.ai-zh.srt").write_text(
                    "1\n00:00:01,000 --> 00:00:02,000\n大家好\n",
                    encoding="utf-8",
                )
                return subprocess_result(0, "", "")

            with mock.patch.object(transcribe, "run", side_effect=run_command):
                result = transcribe.acquire_bilibili_captions(
                    "https://www.bilibili.com/video/BV1abc",
                    output,
                )

            self.assertEqual(len(commands), 2)
            caption_command = commands[1]
            cookie_index = caption_command.index("--cookies-from-browser")
            self.assertEqual(caption_command[cookie_index + 1], "chrome")
            language_index = caption_command.index("--sub-langs")
            self.assertEqual(caption_command[language_index + 1], "ai-zh")
            format_index = caption_command.index("--sub-format")
            self.assertEqual(caption_command[format_index + 1], "srt")
            self.assertIn("--skip-download", caption_command)
            self.assertIn("--write-subs", caption_command)
            self.assertNotIn("bestaudio", caption_command)
            self.assertEqual(result["caption_language"], "ai-zh")
            self.assertFalse(result["doubao_attempted"])
            transcript = Path(result["transcript_path"]).read_text(encoding="utf-8")
            self.assertEqual(transcript, "[00:00:01] 大家好\n")

    def test_bilibili_caption_success_skips_audio_and_doubao(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / "output"
            transcript = output / "source-captions-raw-transcript.txt"
            transcript.parent.mkdir(parents=True)
            transcript.write_text("caption", encoding="utf-8")
            caption_result = {
                "ok": True,
                "engine": "bilibili-platform-captions",
                "transcript_path": str(transcript),
                "doubao_attempted": False,
            }
            argv = [
                "transcribe_media.py",
                "https://www.bilibili.com/video/BV1abc",
                "--output-dir",
                str(output),
            ]
            with (
                mock.patch.object(sys, "argv", argv),
                mock.patch.object(
                    transcribe,
                    "acquire_bilibili_captions",
                    return_value=caption_result,
                ) as captions,
                mock.patch.object(transcribe, "acquire_url_media") as audio,
                mock.patch.object(transcribe, "run") as run_command,
                redirect_stdout(io.StringIO()),
            ):
                transcribe.main()

            captions.assert_called_once()
            audio.assert_not_called()
            run_command.assert_not_called()

    def test_bilibili_caption_failure_falls_back_to_audio(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / "output"
            acquired = output / "source-media.mp3"
            acquired.parent.mkdir(parents=True)
            acquired.write_bytes(b"audio")
            success = subprocess_result(
                0,
                json.dumps(
                    {
                        "ok": True,
                        "mode": "local-base64-flash",
                        "json_path": str(output / "result.json"),
                        "transcript_path": str(output / "result.txt"),
                    }
                ),
                "",
            )
            argv = [
                "transcribe_media.py",
                "https://www.bilibili.com/video/BV1abc",
                "--output-dir",
                str(output),
            ]
            stdout = io.StringIO()
            with (
                mock.patch.object(sys, "argv", argv),
                mock.patch.object(
                    transcribe,
                    "acquire_bilibili_captions",
                    side_effect=RuntimeError("no ai-zh captions"),
                ),
                mock.patch.object(
                    transcribe,
                    "acquire_url_media",
                    return_value=(acquired, "Example"),
                ) as audio,
                mock.patch.object(transcribe, "run", return_value=success),
                redirect_stdout(stdout),
            ):
                transcribe.main()

            audio.assert_called_once()
            result = json.loads(stdout.getvalue())
            self.assertTrue(result["bilibili_captions_attempted"])
            self.assertTrue(result["bilibili_audio_fallback_used"])
            self.assertEqual(
                result["bilibili_caption_error"],
                "no ai-zh captions",
            )

    def test_youtube_caption_failure_falls_back_to_audio(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / "output"
            acquired = output / "source-media.mp3"
            acquired.parent.mkdir(parents=True)
            acquired.write_bytes(b"audio")
            success = subprocess_result(
                0,
                json.dumps(
                    {
                        "ok": True,
                        "mode": "local-base64-flash",
                        "json_path": str(output / "result.json"),
                        "transcript_path": str(output / "result.txt"),
                    }
                ),
                "",
            )
            argv = [
                "transcribe_media.py",
                "https://youtu.be/abc",
                "--output-dir",
                str(output),
            ]
            stdout = io.StringIO()
            with (
                mock.patch.object(sys, "argv", argv),
                mock.patch.object(
                    transcribe,
                    "acquire_youtube_captions",
                    side_effect=RuntimeError("no captions"),
                ),
                mock.patch.object(
                    transcribe,
                    "acquire_url_media",
                    return_value=(acquired, "Example"),
                ),
                mock.patch.object(transcribe, "run", return_value=success),
                redirect_stdout(stdout),
            ):
                transcribe.main()

            result = json.loads(stdout.getvalue())
            self.assertTrue(result["youtube_captions_attempted"])
            self.assertTrue(result["youtube_audio_fallback_used"])
            self.assertEqual(result["youtube_caption_error"], "no captions")

    def test_wrapper_command_contains_only_local_flash_options(self) -> None:
        args = argparse.Namespace(
            output_dir="/tmp/out",
            http_timeout=60.0,
            title=None,
            api_key_file=None,
            local_resource_id=None,
            speaker_info=False,
            no_punc=False,
            plain_text=False,
            dry_run=False,
        )
        command = transcribe.doubao_command(args, "/tmp/source.mp3")
        self.assertIn("/tmp/source.mp3", command)
        for removed in (
            "--public-url",
            "--poll-interval",
            "--max-wait",
            "--resume-request-id",
        ):
            self.assertNotIn(removed, command)

    def test_url_source_is_downloaded_before_flash_command(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            output = root / "output"
            acquired = output / "source-media.mp3"
            acquired.parent.mkdir(parents=True)
            acquired.write_bytes(b"audio")
            success = subprocess_result(
                0,
                json.dumps(
                    {
                        "ok": True,
                        "mode": "local-base64-flash",
                        "json_path": str(output / "result.json"),
                        "transcript_path": str(output / "result.txt"),
                    }
                ),
                "",
            )
            argv = [
                "transcribe_media.py",
                "https://example.com/audio.mp3",
                "--output-dir",
                str(output),
            ]
            captured: list[list[str]] = []

            def run_command(command: list[str]):
                captured.append(command)
                return success

            with (
                mock.patch.object(sys, "argv", argv),
                mock.patch.object(
                    transcribe,
                    "acquire_url_media",
                    return_value=(acquired, "Example"),
                ),
                mock.patch.object(transcribe, "run", side_effect=run_command),
                redirect_stdout(io.StringIO()),
            ):
                transcribe.main()

            self.assertTrue(captured)
            self.assertIn(str(acquired), captured[0])
            self.assertNotIn("https://example.com/audio.mp3", captured[0])


def subprocess_result(
    returncode: int,
    stdout: str,
    stderr: str,
) -> object:
    return type(
        "Completed",
        (),
        {"returncode": returncode, "stdout": stdout, "stderr": stderr},
    )()


if __name__ == "__main__":
    unittest.main()
