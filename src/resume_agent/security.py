import hashlib
import hmac
import threading
import time
from collections import defaultdict, deque
from collections.abc import Callable
from typing import Annotated

from fastapi import Depends, Header, HTTPException, Request, status

from resume_agent.config import Settings, get_settings


def _key_matches(candidate: str, configured: tuple[str, ...]) -> bool:
    candidate_digest = hashlib.sha256(candidate.encode()).digest()
    return any(
        hmac.compare_digest(candidate_digest, hashlib.sha256(key.encode()).digest())
        for key in configured
    )


async def require_api_key(
    settings: Annotated[Settings, Depends(get_settings)],
    x_api_key: Annotated[str | None, Header()] = None,
) -> str:
    if not x_api_key or not _key_matches(x_api_key, settings.api_keys):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid API key")
    return hashlib.sha256(x_api_key.encode()).hexdigest()[:12]


class InMemoryRateLimiter:
    """Thread-safe fixed-window limiter; replace with Redis for multi-instance deployments."""

    def __init__(self, requests: int, window_seconds: int) -> None:
        self.requests = requests
        self.window_seconds = window_seconds
        self._events: dict[str, deque[float]] = defaultdict(deque)
        self._lock = threading.Lock()

    def check(self, identity: str) -> tuple[bool, int]:
        now = time.monotonic()
        cutoff = now - self.window_seconds
        with self._lock:
            events = self._events[identity]
            while events and events[0] <= cutoff:
                events.popleft()
            if len(events) >= self.requests:
                retry_after = max(1, int(self.window_seconds - (now - events[0])))
                return False, retry_after
            events.append(now)
            return True, 0


def rate_limit_dependency(limiter: InMemoryRateLimiter) -> Callable[..., None]:
    def enforce(request: Request, key_id: str = Depends(require_api_key)) -> None:
        identity = f"{key_id}:{request.client.host if request.client else 'unknown'}"
        allowed, retry_after = limiter.check(identity)
        if not allowed:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded",
                headers={"Retry-After": str(retry_after)},
            )

    return enforce
