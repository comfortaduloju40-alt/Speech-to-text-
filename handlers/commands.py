import logging

from telegram import Update
from telegram.ext import ContextTypes

from config import config

logger = logging.getLogger(__name__)


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /start — greet the user and explain the bot."""
    user = update.effective_user
    logger.info(f"User {user.id} ({user.username}) started the bot")

    await update.message.reply_text(
        f"👋 Hello, {user.first_name}!\n\n"
        "I transcribe speech to text. Send me:\n"
        "🎤 A *voice message*\n"
        "🎵 An *audio file*\n"
        "🎬 A *video file*\n\n"
        "I'll return an accurate transcription within seconds.\n\n"
        f"📦 Max file size: *{config.max_file_size_mb}MB*\n"
        f"⚡ Rate limit: *{config.rate_limit_messages} requests "
        f"per {config.rate_limit_window_seconds}s*\n\n"
        "Type /help for more info.",
        parse_mode="Markdown",
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /help — explain supported formats and tips."""
    logger.info(f"User {update.effective_user.id} requested help")

    await update.message.reply_text(
        "🆘 *Help — Speech to Text Bot*\n\n"
        "*Supported input types:*\n"
        "• Voice messages (Telegram native)\n"
        "• Audio files (mp3, m4a, wav, ogg, flac, etc.)\n"
        "• Video files (mp4, mov, avi, mkv, etc.)\n\n"
        "*How it works:*\n"
        "1. Send any audio or video\n"
        "2. I convert it to a Whisper-compatible format\n"
        "3. OpenAI Whisper transcribes it\n"
        "4. You get the text back\n\n"
        "*Tips:*\n"
        "• Clear audio = better accuracy\n"
        "• 99 languages supported (auto-detected)\n"
        "• Keep files under 25MB\n\n"
        "*Having issues?* Make sure your file isn't corrupted "
        "and is under the size limit.",
        parse_mode="Markdown",
    )
