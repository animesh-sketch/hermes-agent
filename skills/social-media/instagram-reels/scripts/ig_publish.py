#!/usr/bin/env python3
"""Publish a Reel to Instagram via the Instagram Graph API.

Usage: ig_publish.py VIDEO_URL --caption "text" --approved [--no-feed] [--dry-run]

Env: IG_USER_ID, IG_ACCESS_TOKEN (never printed), IG_GRAPH_VERSION (default v21.0).
Needs an Instagram Business/Creator account. Publishing requires --approved, which the
agent passes only after the user has replied yes to the preview.
"""
import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

BASE = "https://graph.facebook.com"


def api(method: str, url: str, params: dict) -> dict:
    data = urllib.parse.urlencode(params).encode() if method == "POST" else None
    if method == "GET":
        url = f"{url}?{urllib.parse.urlencode(params)}"
    req = urllib.request.Request(url, data=data, method=method)
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        # Graph errors are JSON and never echo the token.
        raise SystemExit(f"Instagram API error {e.code}: {e.read().decode()[:500]}")


def publish(video_url: str, caption: str, share_to_feed: bool, user: str, token: str,
            version: str, poll_s: float = 5.0, timeout_s: float = 300.0) -> str:
    root = f"{BASE}/{version}"
    c = api("POST", f"{root}/{user}/media", {
        "media_type": "REELS", "video_url": video_url, "caption": caption,
        "share_to_feed": str(share_to_feed).lower(), "access_token": token,
    })
    cid = c["id"]
    deadline = time.monotonic() + timeout_s
    while True:
        st = api("GET", f"{root}/{cid}", {"fields": "status_code,status", "access_token": token})
        code = st.get("status_code")
        if code == "FINISHED":
            break
        if code in ("ERROR", "EXPIRED"):
            raise SystemExit(f"Instagram processing failed: {st}")
        if time.monotonic() > deadline:
            raise SystemExit(f"Timed out waiting for Instagram to process the video: {st}")
        time.sleep(poll_s)
    return api("POST", f"{root}/{user}/media_publish", {"creation_id": cid, "access_token": token})["id"]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("video_url")
    ap.add_argument("--caption", default="")
    ap.add_argument("--no-feed", action="store_true")
    ap.add_argument("--approved", action="store_true", help="user approved this exact Reel")
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()
    if len(a.caption) > 2200:
        print("Caption exceeds 2200 characters", file=sys.stderr)
        return 2
    if a.dry_run:
        print(json.dumps({"dry_run": True, "video_url": a.video_url, "caption_len": len(a.caption)}))
        return 0
    if not a.approved:
        print("Refusing to publish without --approved (get the user's yes first)", file=sys.stderr)
        return 2
    user, token = os.environ.get("IG_USER_ID"), os.environ.get("IG_ACCESS_TOKEN")
    if not user or not token:
        print("IG_USER_ID and IG_ACCESS_TOKEN must be set", file=sys.stderr)
        return 2
    media_id = publish(a.video_url, a.caption, not a.no_feed, user, token,
                       os.environ.get("IG_GRAPH_VERSION", "v21.0"))
    print(json.dumps({"published": True, "media_id": media_id}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
