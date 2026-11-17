#!/usr/bin/env python3
"""Turn a source video into an Instagram-ready 9:16 Reel with ffmpeg.

Usage:
  make_reel.py INPUT --out reel.mp4 [--start 0] [--max-seconds 45]
               [--captions subs.srt] [--music track.mp3] [--music-volume 0.15]
               [--thumb thumb.jpg]
"""
import argparse
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

WIDTH, HEIGHT, FPS = 1080, 1920, 30


def probe_duration(path: Path) -> float:
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "json", str(path)],
        capture_output=True, text=True, check=True,
    ).stdout
    return float(json.loads(out)["format"]["duration"])


def build_filter(captions_name: str | None) -> str:
    vf = (
        f"scale={WIDTH}:{HEIGHT}:force_original_aspect_ratio=increase,"
        f"crop={WIDTH}:{HEIGHT},fps={FPS},setsar=1"
    )
    if captions_name:
        vf += (
            f",subtitles={captions_name}:force_style="
            "'FontSize=14,Bold=1,Outline=2,Alignment=2,MarginV=180'"
        )
    return vf


def build_command(src: Path, out: Path, start: float, duration: float,
                  captions_name: str | None, music: Path | None, music_volume: float) -> list[str]:
    cmd = ["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-ss", f"{start:.3f}", "-t", f"{duration:.3f}", "-i", str(src)]
    if music:
        cmd += ["-stream_loop", "-1", "-i", str(music)]
    cmd += ["-vf", build_filter(captions_name)]
    if music:
        cmd += [
            "-filter_complex",
            f"[0:a]loudnorm=I=-16:TP=-1.5:LRA=11[v];[1:a]volume={music_volume}[m];"
            "[v][m]amix=inputs=2:duration=first:dropout_transition=2[a]",
            "-map", "0:v:0", "-map", "[a]",
        ]
    else:
        cmd += ["-af", "loudnorm=I=-16:TP=-1.5:LRA=11"]
    cmd += [
        "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "128k", "-movflags", "+faststart", "-t", f"{duration:.3f}",
        str(out),
    ]
    return cmd


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("input", type=Path)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--start", type=float, default=0.0)
    ap.add_argument("--max-seconds", type=float, default=45.0)
    ap.add_argument("--captions", type=Path)
    ap.add_argument("--music", type=Path)
    ap.add_argument("--music-volume", type=float, default=0.15)
    ap.add_argument("--thumb", type=Path)
    a = ap.parse_args()

    if not shutil.which("ffmpeg") or not shutil.which("ffprobe"):
        print("ffmpeg/ffprobe not found on PATH", file=sys.stderr)
        return 2
    total = probe_duration(a.input)
    if a.start >= total:
        print(f"--start {a.start} is past the end of the video ({total:.1f}s)", file=sys.stderr)
        return 2
    duration = min(a.max_seconds, total - a.start, 900.0)
    if duration < 3.0:
        print("Reels must be at least 3 seconds long", file=sys.stderr)
        return 2

    # ffmpeg's subtitles filter needs awkward path escaping; run in a temp dir with a plain name.
    with tempfile.TemporaryDirectory() as tmp:
        captions_name = None
        if a.captions:
            captions_name = "subs.srt"
            shutil.copy(a.captions, Path(tmp) / captions_name)
        out = a.out.resolve()
        cmd = build_command(a.input.resolve(), out, a.start, duration, captions_name, a.music, a.music_volume)
        subprocess.run(cmd, check=True, cwd=tmp)
        if a.thumb:
            subprocess.run(
                ["ffmpeg", "-y", "-ss", "1", "-i", str(out), "-frames:v", "1", str(a.thumb.resolve())],
                check=True, capture_output=True,
            )
    print(json.dumps({"reel": str(out), "duration_s": round(duration, 1), "size_bytes": out.stat().st_size}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
