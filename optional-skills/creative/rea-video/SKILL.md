---
name: rea-video
description: Break down how a video was made and plan a remake.
version: 1.0.0
author: animesh-sketch, JuneYaooo (rea-video), Hermes Agent
license: Apache-2.0
platforms: [linux, macos]
prerequisites:
  commands: [ffmpeg, rea-video]
metadata:
  hermes:
    tags: [creative, video, forensics, reels, remake]
    related_skills: [hyperframes]
    category: creative
    requires_toolsets: [terminal]
---

# rea-video Skill

Wraps the open-source `rea-video` CLI (https://github.com/JuneYaooo/rea-video) to reverse-engineer a video shot by shot: filmed, AI-generated, 3D or code-rendered; what overlays, captions and sounds sit on top; how it was edited; and how to remake it. It analyses a video the user supplies. It does not download videos or change them.

## When to Use

- The user shares a reference video and asks how it was made, whether it is AI, or how to copy the style.
- The user wants a remake plan before producing their own Reel.

## Prerequisites

- `ffmpeg` and `ffprobe` on PATH, Python 3.10 or newer.
- Install the CLI once with `terminal`:
  `pip install "rea-video[ocr] @ git+https://github.com/JuneYaooo/rea-video"`
  If pip reports an externally-managed environment, use `pipx install` with the same spec instead. Confirm with `rea-video --help`.
- Optional: a vision-capable model for better accuracy. Set `REA_VLM_BASE_URL`, `REA_VLM_API_KEY`, `REA_VLM_MODEL` in `~/.hermes/.env` and pass `--vlm`. Never print or ask for the key in chat.

## How to Run

```bash
rea-video decompose ref.mp4 -o out/ref --lang en   # add --asr-lang bn for Bengali speech
rea-video summary out/ref/breakdown.json
```

## Quick Reference

| Need | Read |
|------|------|
| Overview, 2k tokens | `out/ref/VIDEO.md` |
| One line per shot | `out/ref/video/timeline.md` |
| One shot in detail | `out/ref/video/shots/<id>.md` and its frames |
| Report for the user | `out/ref/report.html` |

## Procedure

1. Run `decompose`, then `summary`. Check the `VLM:` line: `not_configured` or `failed` means pixel statistics only.
2. Read `VIDEO.md` first; open `timeline.md` and per-shot files only as the question needs. Do not read `breakdown.json`.
3. For every low-confidence shot, open its contact sheet in `shots/` with `vision_analyze`, decide filmed or AI from the image, and say so.
4. Answer with evidence per claim. When unsure, write "to confirm" and what is missing.
5. Give a remake plan: shots, tools, overlays, sound, and which real footage the user must supply.

## Pitfalls

- Without a vision model it often mislabels real phone footage as AI (a real gym clip scored 93% AI in testing). Verify with `vision_analyze` before telling the user.
- Bengali speech needs `--asr-lang bn`; otherwise the transcript is gibberish.
- Analyse only videos the user owns or has permission to study; do not strip watermarks as part of a breakdown.
- The first run downloads models; large clips can take minutes.

## Verification

- `rea-video --help` succeeds.
- `rea-video summary` prints a verdict, per-shot lines and a `VLM:` line.
- `out/ref/VIDEO.md` exists before you answer.
