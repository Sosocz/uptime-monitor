"""
Rate Limiting Module

Provides rate limiting functionality to protect against brute force attacks
and API abuse.
"""
import time
from typing import Dict, Tuple
from collections import defaultdict
from threading import Lock


class RateLimiter:
    """
    Simple in-memory rate limiter using sliding window algorithm.

    For production with multiple workers, consider using Redis-based rate limiting.
    """

    def __init__(self):
        # key -> list of (timestamp, count) tuples
        self.requests: Dict[str, list] = defaultdict(list)
        self.lock = Lock()

    def _clean_old_requests(self, key: str, window_seconds: int):
        """Remove requests older than the window."""
        current_time = time.time()
        cutoff_time = current_time - window_seconds

        with self.lock:
            self.requests[key] = [
                (ts, count) for ts, count in self.requests[key]
                if ts > cutoff_time
            ]

    def is_rate_limited(
        self,
        key: str,
        max_requests: int,
        window_seconds: int
    ) -> Tuple[bool, int]:
        """
        Check if a key is rate limited.

        Args:
            key: Unique identifier (e.g., IP address, user ID, email)
            max_requests: Maximum number of requests allowed in window
            window_seconds: Time window in seconds

        Returns:
            (is_limited, remaining_requests) tuple
            - is_limited: True if rate limit exceeded
            - remaining_requests: Number of requests remaining (0 if limited)
        """
        current_time = time.time()

        # Clean old requests
        self._clean_old_requests(key, window_seconds)

        # Count requests in current window
        with self.lock:
            total_requests = sum(count for _, count in self.requests[key])

            if total_requests >= max_requests:
                return True, 0

            # Add new request
            self.requests[key].append((current_time, 1))
            remaining = max_requests - total_requests - 1

            return False, remaining

    def record_request(self, key: str):
        """Explicitly record a request (used after successful validation)."""
        current_time = time.time()
        with self.lock:
            self.requests[key].append((current_time, 1))

    def reset(self, key: str):
        """Reset rate limit for a specific key."""
        with self.lock:
            if key in self.requests:
                del self.requests[key]


# Global rate limiter instance
rate_limiter = RateLimiter()


# Rate limit configurations
RATE_LIMITS = {
    "login": (5, 300),  # 5 attempts per 5 minutes
    "register": (3, 3600),  # 3 registrations per hour per IP
    "forgot_password": (3, 3600),  # 3 requests per hour
    "reset_password": (5, 3600),  # 5 attempts per hour
    "api_general": (100, 60),  # 100 requests per minute for authenticated API
}


def check_rate_limit(key: str, limit_type: str) -> Tuple[bool, int]:
    """
    Check if rate limit is exceeded for a specific operation.

    Args:
        key: Identifier (IP, email, user_id)
        limit_type: Type of rate limit (login, register, etc.)

    Returns:
        (is_limited, remaining) tuple
    """
    if limit_type not in RATE_LIMITS:
        return False, 999  # No limit configured

    max_requests, window_seconds = RATE_LIMITS[limit_type]
    return rate_limiter.is_rate_limited(
        f"{limit_type}:{key}",
        max_requests,
        window_seconds
    )
