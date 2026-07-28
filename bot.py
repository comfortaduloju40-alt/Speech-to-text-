import logging
import sys
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
)

from config import config
from handlers.commands import start_command, help_command
from handlers.media import (
    handle_voice,
    handle_audio,
    handle_video,
    handle_document,
)


# ── Logging ────────────────────────────────────────────────────────────────────

def setup_logging() -> None:
    """
    Configure logging for the entire application.
    - INFO level for our code
    - WARNING level for noisy third-party libraries
    - Structured format with timestamps
    """
    log_format = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
    date_format = "%Y-%m-%d %H:%M:%S"

    logging.basicConfig(
        level=logging.INFO,
        format=log_format,
        datefmt=date_format,
        handlers=[logging.StreamHandler(sys.stdout)],
    )

    # Suppress noisy third-party loggers
    for noisy_lib in ("httpx", "httpcore", "openai", "telegram"):
        logging.getLogger(noisy_lib).setLevel(logging.WARNING)


logger = logging.getLogger(__name__)


# ── Application Builder ────────────────────────────────────────────────────────

def build_application() -> Application:
    """Create and configure the Telegram Application with all handlers."""

    app = (
        Application.builder()
        .token(config.bot_token)
        .build()
    )

    # Command handlers
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("help", help_command))

    # Media handlers — order matters:
    # voice must come before audio to avoid overlap
    app.add_handler(MessageHandler(filters.VOICE, handle_voice))
    app.add_handler(MessageHandler(filters.AUDIO, handle_audio))
    app.add_handler(MessageHandler(filters.VIDEO, handle_video))
    app.add_handler(MessageHandler(filters.Document.ALL, handle_document))

    # Catch-all for unsupported message types
    app.add_handler(MessageHandler(
        filters.ALL & ~filters.COMMAND & ~filters.VOICE
        & ~filters.AUDIO & ~filters.VIDEO & ~filters.Document.ALL,
        handle_unsupported,
    ))

    logger.info("All handlers registered")
    return app


# ── Fallback Handler ───────────────────────────────────────────────────────────

async def handle_unsupported(update: Update, _) -> None:
    """Gently inform users when they send something the bot can't process."""
    await update.message.reply_text(
        "🤔 I can only transcribe audio and video files.\n\n"
        "Send me a voice message, audio file, or video and I'll convert it to text.\n"
        "Type /help for supported formats."
    )


# ── Entry Point ────────────────────────────────────────────────────────────────

def main() -> None:
    setup_logging()
    logger.info("Starting Speech-to-Text Bot")
    logger.info(f"Mode: {'webhook' if config.use_webhook else 'polling'}")

    app = build_application()

    if config.use_webhook:
        # ── Webhook mode (Railway / production) ───────────────────────────────
        # Railway injects PORT automatically; webhook_url comes from your env
        webhook_path = f"/webhook/{config.webhook_secret}"
        full_webhook_url = f"{config.webhook_url.rstrip('/')}{webhook_path}"

        logger.info(f"Webhook URL: {full_webhook_url}")
        logger.info(f"Listening on port: {config.port}")

        app.run_webhook(
            listen="0.0.0.0",
            port=config.port,
            url_path=webhook_path,
            webhook_url=full_webhook_url,
            secret_token=config.webhook_secret,
            allowed_updates=Update.ALL_TYPES,
        )

    else:
        # ── Polling mode (local development) ──────────────────────────────────
        logger.info("Polling for updates...")
        app.run_polling(
            allowed_updates=Update.ALL_TYPES,
            drop_pending_updates=True,  # ignore messages sent while bot was offline
        )


if __name__ == "__main__":
    main()
