import asyncio
import logging
import os
import uuid
from pathlib import Path

logger = logging.getLogger(__name__)

# Whisper API accepts these formats natively
WHISPER_SUPPORTED_FORMATS = {".mp3", ".mp4", ".mpeg", ".mpga", ".m4a", ".wav", ".webm"}

# Where we store temp files during processing
TEMP_DIR = Path("/tmp/stt_bot")


def ensure_temp_dir() -> None:
    TEMP_DIR.mkdir(parents=True, exist_ok=True)


def generate_temp_path(suffix: str) -> Path:
    return TEMP_DIR / f"{uuid.uuid4().hex}{suffix}"


def needs_conversion(file_extension: str) -> bool:
    return file_extension.lower() not in WHISPER_SUPPORTED_FORMATS


async def convert_to_mp3(input_path: Path) -> Path:
    """
    Convert any audio/video file to mp3 using FFmpeg.
    Returns the path to the converted file.
    """
    output_path = generate_temp_path(".mp3")

    command = [
        "ffmpeg",
        "-i", str(input_path),
        "-vn",                  # strip video stream
        "-ar", "16000",         # 16kHz sample rate (optimal for Whisper)
        "-ac", "1",             # mono channel
        "-b:a", "64k",          # 64kbps bitrate (good quality, small file)
        "-f", "mp3",
        str(output_path),
        "-y",                   # overwrite if exists
        "-loglevel", "error",   # suppress FFmpeg noise
    ]

    logger.info(f"Converting {input_path.name} → mp3")

    process = await asyncio.create_subprocess_exec(
        *command,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )

    _, stderr = await process.communicate()

    if process.returncode != 0:
        error_msg = stderr.decode().strip()
        logger.error(f"FFmpeg conversion failed: {error_msg}")
        raise RuntimeError(f"Audio conversion failed: {error_msg}")

    logger.info(f"Conversion complete → {output_path.name}")
    return output_path


def cleanup_files(*paths: Path) -> None:
    """Remove temp files silently — never let cleanup crash the bot."""
    for path in paths:
        try:
            if path and path.exists():
                os.remove(path)
                logger.debug(f"Cleaned up temp file: {path.name}")
        except Exception as e:
            logger.warning(f"Failed to clean up {path}: {e}")
