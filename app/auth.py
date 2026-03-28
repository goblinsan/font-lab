"""API key authentication dependency and in-memory rate limiter.

Usage in route handlers::

    from app.auth import require_api_key

    @router.get("/protected")
    def protected(key: ApiKey = Depends(require_api_key)):
        ...

The ``X-API-Key`` header is checked against the ``api_keys`` table.  Inactive
keys are rejected with 401.  Each active key has a ``rate_limit`` (requests per
hour); a simple in-memory sliding counter enforces it and returns 429 when the
quota is exceeded.

For the v1 catalog/search/preview endpoints the API key is *optional*: anonymous
callers are allowed but are subject to a shared anonymous rate limit.
"""

from __future__ import annotations

import time
from collections import defaultdict

from fastapi import Depends, Header, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import ApiKey

# ---------------------------------------------------------------------------
# In-memory rate limit store  {key_value: [timestamp, ...]}
# ---------------------------------------------------------------------------
# NOTE: This is an intentionally simple implementation suitable for a
#       single-process deployment.  For multi-process or distributed
#       environments replace with a Redis-backed counter.

_REQUEST_LOG: dict[str, list[float]] = defaultdict(list)
_ANONYMOUS_LIMIT = 100  # requests per hour for unauthenticated callers
_WINDOW_SECONDS = 3600  # 1 hour rolling window


def _check_rate_limit(identity: str, limit: int) -> None:
    """Raise HTTP 429 when *identity* has exceeded *limit* within the window."""
    now = time.time()
    window_start = now - _WINDOW_SECONDS
    log = _REQUEST_LOG[identity]
    # Prune old entries
    log[:] = [t for t in log if t >= window_start]
    if len(log) >= limit:
        raise HTTPException(
            status_code=429,
            detail=f"Rate limit exceeded. Maximum {limit} requests per hour.",
        )
    log.append(now)


# ---------------------------------------------------------------------------
# Dependencies
# ---------------------------------------------------------------------------

def get_api_key(
    x_api_key: str | None = Header(None, alias="X-API-Key"),
    db: Session = Depends(get_db),
) -> ApiKey | None:
    """Return the validated ApiKey record, or ``None`` for anonymous access."""
    if x_api_key is None:
        _check_rate_limit("anonymous", _ANONYMOUS_LIMIT)
        return None

    api_key = db.query(ApiKey).filter(ApiKey.key == x_api_key).first()
    if not api_key or not api_key.is_active:
        raise HTTPException(status_code=401, detail="Invalid or revoked API key.")

    _check_rate_limit(x_api_key, api_key.rate_limit)
    return api_key


def require_api_key(api_key: ApiKey | None = Depends(get_api_key)) -> ApiKey:
    """Like ``get_api_key`` but raises 401 for anonymous callers."""
    if api_key is None:
        raise HTTPException(status_code=401, detail="API key required.")
    return api_key


def require_write_key(api_key: ApiKey = Depends(require_api_key)) -> ApiKey:
    """Require an API key with ``write`` or ``admin`` scope."""
    if api_key.scope not in ("write", "admin"):
        raise HTTPException(status_code=403, detail="Write scope required.")
    return api_key


def require_admin_key(api_key: ApiKey = Depends(require_api_key)) -> ApiKey:
    """Require an API key with ``admin`` scope."""
    if api_key.scope != "admin":
        raise HTTPException(status_code=403, detail="Admin scope required.")
    return api_key
