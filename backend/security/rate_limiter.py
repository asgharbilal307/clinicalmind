"""
Rate Limiter for API calls.
Implements token bucket algorithm for controlling request rates.
"""
import time
import threading
from collections import deque
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class RateLimiter:
    """Token bucket rate limiter for API calls."""

    def __init__(self, requests_per_minute: int = 50, burst_size: int = 10):
        self.rate = requests_per_minute / 60  # per second
        self.burst_size = burst_size
        self.tokens = float(burst_size)
        self.last_update = time.time()
        self.lock = threading.Lock()

    def acquire(self, timeout: float = 30.0) -> bool:
        """Acquire a token, waiting up to timeout seconds."""
        deadline = time.time() + timeout

        while time.time() < deadline:
            with self.lock:
                now = time.time()
                elapsed = now - self.last_update
                self.tokens = min(
                    self.burst_size,
                    self.tokens + elapsed * self.rate
                )
                self.last_update = now

                if self.tokens >= 1:
                    self.tokens -= 1
                    return True

            time.sleep(0.1)  # Check every 100ms

        return False

    def wait_and_acquire(self) -> None:
        """Block until a token is available."""
        while not self.acquire(timeout=30.0):
            logger.warning("Rate limit reached, waiting...")
            time.sleep(1)


class UserRateLimiter:
    """
    Per-user rate limiter using sliding window.
    Tracks requests per user/IP in a time window.
    """

    def __init__(self, max_requests: int = 100, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests: dict[str, deque] = {}
        self.lock = threading.Lock()

    def is_allowed(self, user_id: str) -> bool:
        """Check if user is within rate limit."""
        now = time.time()
        window_start = now - self.window_seconds

        with self.lock:
            if user_id not in self.requests:
                self.requests[user_id] = deque()

            # Remove old requests outside the window
            user_requests = self.requests[user_id]
            while user_requests and user_requests[0] < window_start:
                user_requests.popleft()

            # Check if within limit
            if len(user_requests) >= self.max_requests:
                logger.warning(f"Rate limit exceeded for user: {user_id[:8]}...")
                return False

            # Add current request
            user_requests.append(now)
            return True

    def get_remaining(self, user_id: str) -> int:
        """Get remaining requests for user in current window."""
        now = time.time()
        window_start = now - self.window_seconds

        with self.lock:
            if user_id not in self.requests:
                return self.max_requests

            user_requests = self.requests[user_id]
            # Clean old entries
            while user_requests and user_requests[0] < window_start:
                user_requests.popleft()

            return max(0, self.max_requests - len(user_requests))


# Default rate limiter for external API calls
default_limiter = RateLimiter(requests_per_minute=50, burst_size=10)

# Default user rate limiter for API endpoints
default_user_limiter = UserRateLimiter(max_requests=100, window_seconds=60)