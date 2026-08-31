"""JRE API — Authentication and Rate Limiting.

Provides API key validation and in-memory rate limiting for the
beta staging environment. No changes to engine logic.

Usage::

    from .auth import require_api_key, rate_limiter
"""

from __future__ import annotations

import hashlib
import time
from collections import defaultdict
from typing import Any

from fastapi import Depends, Header, HTTPException, Request


# ── Mock API Keys (Beta Testers) ───────────────────────────────────────────

# These are mock keys for beta testing. In production, these would be
# stored in a database and hashed.
_BETA_API_KEYS: dict[str, dict[str, Any]] = {
    "jre-beta-key-alpha": {
        "name": "Beta Tester A",
        "tier": "standard",
    },
    "jre-beta-key-beta": {
        "name": "Beta Tester B",
        "tier": "standard",
    },
    "jre-beta-key-gamma": {
        "name": "Beta Tester C",
        "tier": "standard",
    },
}

# Public API key for docs/readme access (read-only)
_PUBLIC_API_KEY = "jre-public-read"


# ── API Key Validation ──────────────────────────────────────────────────────

def _hash_key(api_key: str) -> str:
    """Hash an API key for secure storage/comparison."""
    return hashlib.sha256(api_key.encode()).hexdigest()[:16]


async def require_api_key(
    x_api_key: str = Header(
        ...,
        description="API key for authentication",
        alias="X-API-Key",
    ),
) -> dict[str, Any]:
    """FastAPI dependency that validates the X-API-Key header.

    Returns the key metadata dict if valid.
    Raises HTTPException 401 if the key is invalid.
    """
    if x_api_key not in _BETA_API_KEYS:
        raise HTTPException(
            status_code=401,
            detail="Invalid or missing API key. Obtain a key from the JRE beta program.",
            headers={"WWW-Authenticate": "ApiKey"},
        )
    return _BETA_API_KEYS[x_api_key]


def get_key_hash(api_key: str) -> str:
    """Return a hashed version of the API key for logging (PII-safe)."""
    return _hash_key(api_key)


# ── Rate Limiter ────────────────────────────────────────────────────────────

class InMemoryRateLimiter:
    """Simple in-memory sliding window rate limiter.

    Tracks request timestamps per API key and enforces a maximum
    number of requests within a rolling time window.
    """

    def __init__(
        self,
        max_requests: int = 10,
        window_seconds: int = 60,
    ) -> None:
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._requests: dict[str, list[float]] = defaultdict(list)

    def _clean_window(self, key: str, now: float) -> None:
        """Remove timestamps outside the sliding window."""
        cutoff = now - self.window_seconds
        self._requests[key] = [
            ts for ts in self._requests[key] if ts > cutoff
        ]

    def is_allowed(self, key: str) -> bool:
        """Check if a request is allowed for the given key.

        Args:
            key: The API key or identifier.

        Returns:
            True if the request is within rate limits, False otherwise.
        """
        now = time.time()
        self._clean_window(key, now)

        if len(self._requests[key]) >= self.max_requests:
            return False

        self._requests[key].append(now)
        return True

    def remaining(self, key: str) -> int:
        """Return remaining requests in the current window."""
        now = time.time()
        self._clean_window(key, now)
        return max(0, self.max_requests - len(self._requests[key]))

    def reset_time(self, key: str) -> float:
        """Return seconds until the oldest request in the window expires."""
        now = time.time()
        self._clean_window(key, now)
        if not self._requests[key]:
            return 0.0
        oldest = self._requests[key][0]
        return max(0.0, self.window_seconds - (now - oldest))


# Global rate limiter instance
# Configurable via environment: JRE_RATE_LIMIT_MAX and JRE_RATE_LIMIT_WINDOW
import os
_rate_limit_max = int(os.environ.get("JRE_RATE_LIMIT_MAX", "10"))
_rate_limit_window = int(os.environ.get("JRE_RATE_LIMIT_WINDOW", "60"))
rate_limiter = InMemoryRateLimiter(max_requests=_rate_limit_max, window_seconds=_rate_limit_window)


async def check_rate_limit(
    request: Request,
    api_key_meta: dict[str, Any] = Depends(require_api_key),
) -> dict[str, Any]:
    """FastAPI dependency that combines API key auth with rate limiting.

    Returns the key metadata dict if the request is allowed.
    Raises HTTPException 429 if rate limit is exceeded.
    """
    # Use a stable key identifier (the original key string, not the metadata)
    # We extract it from the request headers
    raw_key = request.headers.get("X-API-Key", "")

    if not rate_limiter.is_allowed(raw_key):
        retry_after = rate_limiter.reset_time(raw_key)
        raise HTTPException(
            status_code=429,
            detail=(
                f"Rate limit exceeded. Maximum {rate_limiter.max_requests} "
                f"requests per {rate_limiter.window_seconds} seconds. "
                f"Retry after {retry_after:.0f}s."
            ),
            headers={
                "Retry-After": str(int(retry_after)),
                "X-RateLimit-Limit": str(rate_limiter.max_requests),
                "X-RateLimit-Remaining": "0",
            },
        )

    return api_key_meta
