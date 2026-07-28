import os
from dataclasses import dataclass, field
from dotenv import load_dotenv

load_dotenv()


def _require(key: str) -> str:
    value = os.getenv(key)
    if not value:
        raise EnvironmentError(f"Required environment variable '{key}' is not set.")
    return value


@dataclass(frozen=True)
class Config:
    # Required
    bot_token: str = field(default_factory=lambda: _require("BOT_TOKEN"))
    openai_api_key: str = field(default_factory=lambda: _require("OPENAI_API_KEY"))

    # Webhook (optional — falls back to polling if not set)
    webhook_url: str = field(default_factory=lambda: os.getenv("WEBHOOK_URL", ""))
    webhook_secret: str = field(default_factory=lambda: os.getenv("WEBHOOK_SECRET", ""))
    port: int = field(default_factory=lambda: int(os.getenv("PORT", "8000")))

    # File handling
    max_file_size_mb: int = field(
        default_factory=lambda: int(os.getenv("MAX_FILE_SIZE_MB", "25"))
    )

    # Rate limiting
    rate_limit_messages: int = field(
        default_factory=lambda: int(os.getenv("RATE_LIMIT_MESSAGES", "5"))
    )
    rate_limit_window_seconds: int = field(
        default_factory=lambda: int(os.getenv("RATE_LIMIT_WINDOW_SECONDS", "60"))
    )

    # Derived
    @property
    def max_file_size_bytes(self) -> int:
        return self.max_file_size_mb * 1024 * 1024

    @property
    def use_webhook(self) -> bool:
        return bool(self.webhook_url)


config = Config()
