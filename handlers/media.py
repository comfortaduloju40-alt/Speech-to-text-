import logging
from pathlib import Path

from telegram import Update, Message
from telegram.ext import ContextTypes
from telegram.constants import ChatAction

from config import config
from services.audio_converter import (
    convert_to_mp3,
    cleanup_files,
    ensure_temp_dir,
    generate_temp_path,
    needs_conversion,
)
from services.transcription import transcribe_audio
from utils.rate_limiter import rate_limiter

logger = logging.getLogger(__name__)


async def _check_rate_limit(message: Message, user_id: int) -> bool:
    """Returns True if request is allowed, False if rate limited."""
    if not rate_limiter.is_allowed(user_id):
        wait = rate_limiter.seconds_until_reset(user_id)
        await message.reply_text(
            f"⏳ You're sending too fast. Please wait *{wait}s* before trying again.",
            parse_mode="Markdown",
        )
        return False
    return True


async def _validate_file_size(message: Message, file_size: int | None) -> bool:
    """Returns True if file is within the allowed size limit."""
    if file_size and file_size > config.max_file_size_bytes:
        size_mb = file_size / (1024 * 1024)
        await message.reply_text(
            f"❌ File too large ({size_mb:.1f}MB). "
            f"Maximum allowed size is *{config.max_file_size_mb}MB*.",
            parse_mode="Markdown",
        )
        return False
    return True


async def _download_file(message: Message, file_id: str, suffix: str) -> Path | None:
    """Download a Telegram file to a local temp path. Returns None on failure."""
    ensure_temp_dir()
    dest = generate_temp_path(suffix)

    try:
        tg_file = await message.get_bot().get_file(file_id)
        await tg_file.download_to_drive(dest)
        logger.info(f"Downloaded file {file_id} → {dest.name}")
        return dest
    except Exception as e:
        logger.error(f"Failed to download file {file_id}: {e}")
        await message.reply_text(
            "❌ Failed to download your file from Telegram. Please try again."
        )
        return None


async def _process_media(
    message: Message,
    file_id: str,
    file_size: int | None,
    original_suffix: str,
) -> None:
    """
    Core pipeline:
    download → convert (if needed) → transcribe → reply
    """
    user_id = message.from_user.id
    downloaded_path: Path | None = None
    converted_path: Path | None = None

    try:
        # 1. Rate limit check
        if not await _check_rate_limit(message, user_id):
            return

        # 2. File size check
        if not await _validate_file_size(message, file_size):
            return

        # 3. Show activity indicator
        await message.reply_chat_action(ChatAction.TYPING)
        status_msg = await message.reply_text("⏳ Downloading your file...")

        # 4. Download from Telegram
        downloaded_path = await _download_file(message, file_id, original_suffix)
        if not downloaded_path:
            return

        # 5. Convert if format not natively supported by Whisper
        await status_msg.edit_text("🔄 Converting audio format...")
        await message.reply_chat_action(ChatAction.TYPING)

        if needs_conversion(original_suffix):
            converted_path = await convert_to_mp3(downloaded_path)
            transcription_input = converted_path
        else:
            transcription_input = downloaded_path

        # 6. Transcribe
        await status_msg.edit_text("🎧 Transcribing... this may take a moment.")
        await message.reply_chat_action(ChatAction.TYPING)

        transcript = await transcribe_audio(transcription_input)

        # 7. Reply with result
        await status_msg.delete()
        await message.reply_text(transcript)

        logger.info(
            f"Transcription delivered to user {user_id} "
            f"({len(transcript)} chars)"
        )

    except RuntimeError as e:
        # FFmpeg or Whisper errors — user-facing
        logger.error(f"Processing error for user {user_id}: {e}")
        await message.reply_text(
            f"❌ Processing failed: {e}\n\nPlease check your file and try again."
        )

    except Exception as e:
        # Unexpected errors — generic message to user, full log for us
        logger.exception(f"Unexpected error for user {user_id}: {e}")
        await message.reply_text(
            "❌ Something went wrong on our end. Please try again in a moment."
        )

    finally:
        # Always clean up temp files, even if something crashed
        cleanup_files(downloaded_path, converted_path)


# ── Public handler functions registered with the bot ──────────────────────────

async def handle_voice(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle Telegram voice messages (.ogg/opus)."""
    voice = update.message.voice
    logger.info(f"Voice message from user {update.effective_user.id} ({voice.duration}s)")
    await _process_media(
        message=update.message,
        file_id=voice.file_id,
        file_size=voice.file_size,
        original_suffix=".ogg",
    )


async def handle_audio(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle audio files sent as documents or audio attachments."""
    audio = update.message.audio
    # Extract extension from mime type or filename
    suffix = _get_suffix(audio.file_name, audio.mime_type, ".mp3")
    logger.info(f"Audio file from user {update.effective_user.id}: {audio.file_name}")
    await _process_media(
        message=update.message,
        file_id=audio.file_id,
        file_size=audio.file_size,
        original_suffix=suffix,
    )


async def handle_video(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle video files — FFmpeg will extract the audio track."""
    video = update.message.video
    suffix = _get_suffix(video.file_name, video.mime_type, ".mp4")
    logger.info(f"Video file from user {update.effective_user.id}: {video.file_name}")
    await _process_media(
        message=update.message,
        file_id=video.file_id,
        file_size=video.file_size,
        original_suffix=suffix,
    )


async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle files sent as generic documents.
    Telegram sometimes delivers audio/video as 'document' type.
    We validate the mime type before processing.
    """
    doc = update.message.document
    mime = doc.mime_type or ""

    if not (mime.startswith("audio/") or mime.startswith("video/")):
        await update.message.reply_text(
            "❌ Unsupported file type. Please send an audio or video file."
        )
        return

    suffix = _get_suffix(doc.file_name, mime, ".mp3")
    logger.info(f"Document ({mime}) from user {update.effective_user.id}: {doc.file_name}")
    await _process_media(
        message=update.message,
        file_id=doc.file_id,
        file_size=doc.file_size,
        original_suffix=suffix,
    )


def _get_suffix(filename: str | None, mime_type: str | None, fallback: str) -> str:
    """Derive file extension from filename, then mime type, then fallback."""
    if filename:
        suffix = Path(filename).suffix.lower()
        if suffix:
            return suffix

    _mime_map = {
        "audio/mpeg": ".mp3",
        "audio/mp4": ".m4a",
        "audio/ogg": ".ogg",
        "audio/wav": ".wav",
        "audio/webm": ".webm",
        "audio/flac": ".flac",
        "video/mp4": ".mp4",
        "video/quicktime": ".mov",
        "video/x-msvideo": ".avi",
        "video/webm": ".webm",
        "video/x-matroska": ".mkv",
    }

    return _mime_map.get(mime_type or "", fallback)
