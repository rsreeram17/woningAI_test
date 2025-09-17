"""Rate limiting utilities for API clients."""

import time
from typing import Dict, Any
from threading import Lock

class RateLimiter:
    """Rate limiter for API calls."""

    def __init__(self, config: Dict[str, Any]):
        """Initialize rate limiter with configuration."""
        self.requests_per_second = config.get('requests_per_second', 50)
        self.requests_per_day = config.get('requests_per_day', 100000)

        self.last_request_time = 0
        self.daily_request_count = 0
        self.daily_reset_time = time.time()
        self._lock = Lock()

    def wait_if_needed(self):
        """Wait if necessary to respect rate limits."""
        with self._lock:
            current_time = time.time()

            # Reset daily counter if needed
            if current_time - self.daily_reset_time > 86400:  # 24 hours
                self.daily_request_count = 0
                self.daily_reset_time = current_time

            # Check daily limit
            if self.daily_request_count >= self.requests_per_day:
                raise Exception(f"Daily rate limit exceeded ({self.requests_per_day} requests/day)")

            # Check per-second limit
            time_since_last = current_time - self.last_request_time
            min_interval = 1.0 / self.requests_per_second

            if time_since_last < min_interval:
                sleep_time = min_interval - time_since_last
                time.sleep(sleep_time)

            self.last_request_time = time.time()
            self.daily_request_count += 1

    def get_stats(self) -> Dict[str, Any]:
        """Get rate limiter statistics."""
        current_time = time.time()
        return {
            'requests_today': self.daily_request_count,
            'daily_limit': self.requests_per_day,
            'requests_per_second_limit': self.requests_per_second,
            'time_since_last_request': current_time - self.last_request_time
        }