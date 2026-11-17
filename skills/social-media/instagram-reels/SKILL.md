---
name: instagram-reels
description: "Edit a sent video into a Reel and post it to Instagram."
version: 1.0.0
author: animesh-sketch, Hermes Agent
license: MIT
platforms: [linux, macos]
prerequisites:
  commands: [ffmpeg, ffprobe]
metadata:
  hermes:
    tags: [instagram, reels, video, social-media, telegram]
    category: social-media
---

# Instagram Reels Skill

Turns a video the user sends into a 9:16 Reel, shows a preview and caption for approval,
then publishes it through the Instagram Graph API. It never posts without a yes, and it
does not invent footage: it edits only what the user sent.

## When to Use

- The user sends a video (usually on Telegram) and wants it posted as a Reel.
- A scheduled reminder asked for today's video and the user replied with one.

## Prerequisites

- `ffmpeg` and `ffprobe` on PATH.
- Instagram Business or Creator account linked to a Facebook Page, with a Graph API
  long-lived token. Set `IG_USER_ID` and `IG_ACCESS_TOKEN` in `~/.hermes/.env`.
- S3-compatible storage for the public video URL: `REEL_S3_BUCKET`, optional
  `REEL_S3_ENDPOINT` (for example Cloudflare R2), AWS-style key env vars, and `pip install boto3`.
- Never print, read back or ask for the token in chat. Check only that the env vars exist.

## How to Run

Scripts live in this skill's `scripts/` directory; run them with `terminal`.

```bash
python scripts/make_reel.py IN.mp4 --out reel.mp4 --thumb thumb.jpg [--captions subs.srt] [--music bg.mp3]
python scripts/host_video.py reel.mp4          # prints a time-limited public URL
python scripts/ig_publish.py URL --caption "..." --approved
```

## Quick Reference

| Step | Tool | Output |
|------|------|--------|
| Edit | `make_reel.py` | `reel.mp4`, `thumb.jpg` |
| Preview | send file to user | approval or edits |
| Host | `host_video.py` | public URL |
| Publish | `ig_publish.py --approved` | media id |

## Procedure

1. Save the incoming video, then `vision_analyze` a few frames to understand it.
2. Pick the best segment (3-60 s; default 45 s) and run `make_reel.py`. If there is speech,
   transcribe it, write an `.srt`, and pass `--captions`.
3. Write a hook-first caption with 3-8 relevant hashtags (max 2200 chars).
4. Send the Reel, thumbnail and caption to the user and ask: "Post this? yes / edit / skip".
5. Only on an explicit yes: `host_video.py`, then `ig_publish.py --approved`.
6. Report the media id or the exact error. On "edit", revise and repeat from step 4.

## Pitfalls

- Never pass `--approved` without a yes for this exact Reel; an earlier yes does not carry over.
- The presigned URL must stay valid until Instagram finishes processing; use the default 6 h.
- Instagram rejects videos under 3 s or over 15 min; keep Reels at 90 s or less for reach.
- Graph tokens expire (about 60 days); a 190 error means the user must refresh the token.
- Instagram allows about 50 API-published posts per 24 h; twice a day is far below that.

## Verification

- `ffprobe reel.mp4` reports 1080x1920, H.264/AAC, 3 s or longer.
- `ig_publish.py URL --dry-run` succeeds before the first live post.
- After publishing, confirm the media id with the user.
