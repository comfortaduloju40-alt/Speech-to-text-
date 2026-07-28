import time
import logging
from collections import defaultdict

from config import config

logger = logging.getLogger(__name__)


class RateLimiter:
    """
    Sliding window rate limiter.
    Tracks how many requests each user has made within the time window.
    """

    def __init__(self) -> None:
        # user_id → list of timestamps
        self._user_timestamps: dict[int, list[float]] = defaultdict(list)

    def is_allowed(self, user_id: int) -> bool:
        now = time.monotonic()
        window = config.rate_limit_window_seconds
        limit = config.rate_limit_messages

        # Keep only timestamps within the current window
        timestamps = self._user_timestamps[user_id]
        self._user_timestamps[user_id] = [
            ts for ts in timestamps if now - ts < window
        ]

        if len(self._user_timestamps[user_id]) >= limit:
            logger.warning(f"Rate limit hit for user {user_id}")
            return False

        self._user_timestamps[user_id].append(now)
        return True

    def seconds_until_reset(self, user_id: int) -> int:
        """Returns how many seconds until the user's oldest request expires."""
        now = time.monotonic()
        window = config.rate_limit_window_seconds
        timestamps = self._user_timestamps.get(user_id, [])

        if not timestamps:
            return 0

        oldest = min(timestamps)
        return max(0, int(window - (now - oldest)))


# Single shared instance used across all handlers
rate_limiter = RateLimiter()
