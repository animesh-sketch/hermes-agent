#!/usr/bin/env python3
"""Upload a file to S3-compatible storage and print a time-limited public URL.

Instagram fetches the Reel from a URL, so the file must be reachable from the internet.
Env: REEL_S3_BUCKET (required), REEL_S3_ENDPOINT (optional, e.g. Cloudflare R2),
     REEL_S3_REGION (default auto), AWS_ACCESS_KEY_ID / AWS_SECRET_ACCESS_KEY.
Requires: pip install boto3
"""
import argparse
import os
import sys
import uuid
from pathlib import Path


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("file", type=Path)
    ap.add_argument("--expires", type=int, default=6 * 3600, help="URL lifetime in seconds")
    a = ap.parse_args()
    bucket = os.environ.get("REEL_S3_BUCKET")
    if not bucket:
        print("REEL_S3_BUCKET is not set", file=sys.stderr)
        return 2
    try:
        import boto3
    except ImportError:
        print("boto3 missing: pip install boto3", file=sys.stderr)
        return 2
    s3 = boto3.client(
        "s3",
        endpoint_url=os.environ.get("REEL_S3_ENDPOINT") or None,
        region_name=os.environ.get("REEL_S3_REGION", "auto"),
    )
    key = f"reels/{uuid.uuid4().hex}{a.file.suffix or '.mp4'}"
    s3.upload_file(str(a.file), bucket, key, ExtraArgs={"ContentType": "video/mp4"})
    print(s3.generate_presigned_url("get_object", Params={"Bucket": bucket, "Key": key}, ExpiresIn=a.expires))
    return 0


if __name__ == "__main__":
    sys.exit(main())
