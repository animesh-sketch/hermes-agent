# Setup: twice-daily Reel agent on a VPS

1. Install Hermes from this fork on the VPS, then `hermes model` to pick a provider.
2. Telegram: create a bot with @BotFather (or the dashboard "Create with QR" button). In
   `~/.hermes/.env` set `TELEGRAM_BOT_TOKEN` and `TELEGRAM_ALLOWED_USERS=<your numeric id>`.
   Only you may talk to the bot. Run `hermes gateway setup`, then `hermes gateway start`.
3. Instagram: convert the account to Business or Creator, link it to a Facebook Page, create a
   Meta developer app with `instagram_content_publish`, and generate a long-lived token. Put
   `IG_USER_ID` and `IG_ACCESS_TOKEN` in `~/.hermes/.env` yourself (never in chat).
4. Storage: create a bucket (Cloudflare R2 or S3), set `REEL_S3_BUCKET`, `REEL_S3_ENDPOINT`,
   the key env vars, and `pip install boto3` in Hermes' environment.
5. Schedule two daily prompts (replace the timezone). In a Telegram chat with the bot, send:

   "Every day at 09:00 and 19:00 Asia/Kolkata, message me asking for today's video for my
   Instagram Reel. When I send it, use the instagram-reels skill."

   or via CLI, one job per time with delivery to your Telegram chat:
   `hermes cron create "0 9 * * *" --timezone Asia/Kolkata "Ask me for the video for the morning Reel."`
   `hermes cron create "0 19 * * *" --timezone Asia/Kolkata "Ask me for the video for the evening Reel."`
6. Dry run before going live: send a video, approve the preview, and check the post appears.
   `python scripts/ig_publish.py URL --dry-run` validates arguments without posting.
