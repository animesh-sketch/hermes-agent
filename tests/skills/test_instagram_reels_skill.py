"""Tests for the instagram-reels skill scripts (no network, no ffmpeg required)."""
import importlib.util
from pathlib import Path
from unittest.mock import patch

import pytest

SCRIPTS = Path(__file__).resolve().parents[2] / "skills" / "social-media" / "instagram-reels" / "scripts"


def _load(name):
    spec = importlib.util.spec_from_file_location(name, SCRIPTS / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


make_reel = _load("make_reel")
ig_publish = _load("ig_publish")


def test_filter_crops_to_9_16():
    vf = make_reel.build_filter(None)
    assert "1080:1920" in vf and "subtitles" not in vf


def test_filter_burns_captions():
    assert "subtitles=subs.srt" in make_reel.build_filter("subs.srt")


def test_command_with_music_mixes_audio():
    cmd = make_reel.build_command(Path("a.mp4"), Path("o.mp4"), 2.0, 30.0, None, Path("m.mp3"), 0.2)
    joined = " ".join(cmd)
    assert "amix" in joined and "volume=0.2" in joined and "+faststart" in joined


def test_publish_requires_approval(capsys):
    with patch("sys.argv", ["ig_publish.py", "https://x/y.mp4", "--caption", "hi"]):
        assert ig_publish.main() == 2
    assert "--approved" in capsys.readouterr().err


def test_dry_run_needs_no_credentials(capsys):
    with patch("sys.argv", ["ig_publish.py", "https://x/y.mp4", "--dry-run"]):
        assert ig_publish.main() == 0


def test_publish_flow_polls_until_finished():
    calls = []

    def fake_api(method, url, params):
        calls.append((method, url.rsplit("/", 1)[-1]))
        if url.endswith("/media"):
            return {"id": "C1"}
        if url.endswith("/C1"):
            return {"status_code": "FINISHED"}
        return {"id": "M1"}

    with patch.object(ig_publish, "api", fake_api):
        assert ig_publish.publish("https://x/y.mp4", "cap", True, "U", "T", "v21.0", poll_s=0) == "M1"
    assert calls[0] == ("POST", "media") and calls[-1] == ("POST", "media_publish")


def test_publish_fails_on_processing_error():
    def fake_api(method, url, params):
        return {"id": "C1"} if url.endswith("/media") else {"status_code": "ERROR"}

    with patch.object(ig_publish, "api", fake_api), pytest.raises(SystemExit):
        ig_publish.publish("https://x/y.mp4", "", True, "U", "T", "v21.0", poll_s=0)
