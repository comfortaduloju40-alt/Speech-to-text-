# 🎙️ Telegram Speech-to-Text Bot

A production-ready Telegram bot that transcribes voice messages, audio files,
and video files to text using OpenAI Whisper.

## Features

- 🎤 Voice messages
- 🎵 Audio files (mp3, m4a, wav, ogg, flac, and more)
- 🎬 Video files (mp4, mov, avi, mkv, webm, and more)
- 🌍 99 languages — auto-detected
- ⚡ Rate limiting per user
- 📦 Max file size validation
- 🔄 Progress messages during processing
- 🧹 Automatic temp file cleanup

---

## Project Structure

```
├── bot.py                  # Entry point
├── config.py               # Environment-based configuration
├── handlers/
│   ├── commands.py         # /start and /help
│   └── media.py            # Voice, audio, video, document handling
├── services/
│   ├── audio_converter.py  # FFmpeg conversion
│   └── transcription.py    # OpenAI Whisper API
├── utils/
│   └── rate_limiter.py     # Sliding window rate limiter
├── Dockerfile
├── railway.json
├── requirements.txt
└── .env.example
```

---

## Environment Variables

| Variable | Required | Default | Description |
|---|---|---|---|
| `BOT_TOKEN` | ✅ | — | Telegram bot token from @BotFather |
| `OPENAI_API_KEY` | ✅ | — | OpenAI API key for Whisper |
| `WEBHOOK_URL` | ⚠️ Production | — | Your Railway public URL |
| `WEBHOOK_SECRET` | ⚠️ Production | — | Random secret string for webhook security |
| `PORT` | Auto | `8000` | Set automatically by Railway |
| `MAX_FILE_SIZE_MB` | ❌ | `25` | Maximum upload size in MB |
| `RATE_LIMIT_MESSAGES` | ❌ | `5` | Max requests per window per user |
| `RATE_LIMIT_WINDOW_SECONDS` | ❌ | `60` | Rate limit window in seconds |

---

## Local Setup

### Prerequisites

- Python 3.12+
- FFmpeg installed
- A Telegram bot token ([create one with @BotFather](https://t.me/BotFather))
- An OpenAI API key ([platform.openai.com](https://platform.openai.com))

### FFmpeg Installation

**macOS:**
```bash
brew install ffmpeg
```

**Ubuntu / Debian:**
```bash
sudo apt update && sudo apt install ffmpeg
```

**Windows:**
Download from [ffmpeg.org](https://ffmpeg.org/download.html) and add
the `bin/` folder to your system PATH.

Verify installation:
```bash
ffmpeg -version
```

### Install and Run

```bash
# 1. Clone the repo
git clone https://github.com/YOUR_USERNAME/YOUR_REPO.git
cd YOUR_REPO

# 2. Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment
cp .env.example .env
# Edit .env and fill in BOT_TOKEN and OPENAI_API_KEY
# Leave WEBHOOK_URL empty for local polling mode

# 5. Run
python bot.py
```

---

## GitHub Deployment

```bash
# 1. Initialise git (if not already done)
git init
git add .
git commit -m "Initial commit — Telegram STT bot"

# 2. Create a new repo on github.com, then:
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO.git
git branch -M main
git push -u origin main
```

---

## Railway Deployment

### First Deployment

1. Go to [railway.app](https://railway.app) and sign in with GitHub
2. Click **New Project → Deploy from GitHub repo**
3. Select your repository
4. Railway detects the `Dockerfile` automatically via `railway.json`

### Set Environment Variables on Railway

In your Railway project dashboard:

1. Click your service → **Variables** tab
2. Add the following:

```
BOT_TOKEN=your_telegram_bot_token
OPENAI_API_KEY=your_openai_api_key
WEBHOOK_SECRET=any_long_random_string_you_choose
```

3. After the first deploy completes, copy your Railway public URL:
   - Go to **Settings → Networking → Generate Domain**
   - It looks like: `https://your-app.up.railway.app`

4. Add one more variable:
```
WEBHOOK_URL=https://your-app.up.railway.app
```

5. Railway will automatically redeploy with the new variables.

### Subsequent Deployments

Every push to `main` triggers an automatic redeploy:

```bash
git add .
git commit -m "Your change description"
git push
```

---

## Troubleshooting

### Bot doesn't respond locally
- Check that `BOT_TOKEN` is set correctly in `.env`
- Make sure `WEBHOOK_URL` is empty in `.env` (forces polling mode)
- Confirm your bot is not already running elsewhere (only one polling instance allowed)

### FFmpeg errors
- Run `ffmpeg -version` to confirm it's installed and on PATH
- On Windows, ensure the FFmpeg `bin/` folder is in your system PATH

### File too large error
- Whisper API has a hard 25MB limit
- Reduce `MAX_FILE_SIZE_MB` if you want a lower limit
- For larger files, you would need to implement chunking

### Webhook not receiving updates (Railway)
- Confirm `WEBHOOK_URL` matches your Railway domain exactly (no trailing slash)
- Confirm `WEBHOOK_SECRET` is set and matches on both ends
- Check Railway logs: **Dashboard → your service → Logs tab**

### Rate limit errors from OpenAI
- You've hit your OpenAI API tier limits
- Check usage at [platform.openai.com/usage](https://platform.openai.com/usage)
- Consider upgrading your OpenAI plan for higher throughput

### Railway build fails
- Check that `railway.json` points to `Dockerfile` correctly
- Review the build logs in the Railway dashboard

---

## Cost Estimate

OpenAI Whisper API pricing: **$0.006 per minute of audio**

| Usage | Monthly Cost |
|---|---|
| 100 minutes/month | ~$0.60 |
| 1,000 minutes/month | ~$6.00 |
| 10,000 minutes/month | ~$60.00 |

Railway hosting: free hobby tier available, or ~$5/month for always-on.
