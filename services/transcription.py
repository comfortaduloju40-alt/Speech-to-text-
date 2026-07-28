import logging
from pathlib import Path

from openai import AsyncOpenAI

from config import config

logger = logging.getLogger(__name__)

# Lazily instantiated so we don't create the client at import time
_client: AsyncOpenAI | None = None


def get_openai_client() -> AsyncOpenAI:
    global _client
    if _client is None:
        _client = AsyncOpenAI(api_key=config.openai_api_key)
    return _client


async def transcribe_audio(audio_path: Path) -> str:
    """
    Send an audio file to the OpenAI Whisper API and return the transcript.

    Whisper API handles:
    - Files up to 25MB
    - Long audio automatically (no manual chunking needed)
    - 99 languages with auto-detection
    """
    client = get_openai_client()

    logger.info(f"Sending {audio_path.name} to Whisper API ({audio_path.stat().st_size / 1024:.1f} KB)")

    with open(audio_path, "rb") as audio_file:
        response = await client.audio.transcriptions.create(
            model="whisper-1",
            file=audio_file,
            response_format="text",     # returns plain string, not JSON
            temperature=0.0,            # deterministic output
        )

    # When response_format="text", the SDK returns the string directly
    transcript = response.strip() if isinstance(response, str) else str(response).strip()

    if not transcript:
        return "⚠️ No speech detected in the audio."

    logger.info(f"Transcription complete — {len(transcript)} characters")
    return transcript
