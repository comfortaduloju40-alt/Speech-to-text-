# ── Base image ─────────────────────────────────────────────────────────────────
FROM python:3.12-slim

# Prevents Python from writing .pyc files and enables unbuffered logs
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# ── System dependencies ────────────────────────────────────────────────────────
# FFmpeg is required for audio/video conversion
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# ── Working directory ──────────────────────────────────────────────────────────
WORKDIR /app

# ── Python dependencies ────────────────────────────────────────────────────────
# Copy requirements first so Docker caches this layer
# Only re-runs pip install when requirements.txt changes
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# ── Application code ───────────────────────────────────────────────────────────
COPY . .

# ── Temp directory for audio processing ───────────────────────────────────────
RUN mkdir -p /tmp/stt_bot

# ── Non-root user for security ─────────────────────────────────────────────────
RUN useradd --create-home --shell /bin/bash botuser \
    && chown -R botuser:botuser /app \
    && chown -R botuser:botuser /tmp/stt_bot

USER botuser

# ── Entrypoint ─────────────────────────────────────────────────────────────────
CMD ["python", "bot.py"]
