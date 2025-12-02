import os
import time
from collections import deque, defaultdict
from typing import Deque, Dict, Tuple

from fastapi import Request, HTTPException


_WINDOW_SEC = int(os.getenv("RATE_LIMIT_WINDOW_SEC", "60"))
_MAX_REQ = int(os.getenv("RATE_LIMIT_MAX_REQUESTS", "120"))

# Optional per-path limits via JSON env: {"/api/v1/ai/chat": [30, 10], "/api/v1/rag/search": [60, 30]}
import json
_PER_PATH_RAW = os.getenv("RATE_LIMITS_JSON")
try:
    _PER_PATH = json.loads(_PER_PATH_RAW) if _PER_PATH_RAW else {}
except Exception:
    _PER_PATH = {}

# key -> deque of timestamps (seconds)
_buckets: Dict[str, Deque[float]] = defaultdict(deque)


def _client_key(request: Request) -> str:
    fwd = request.headers.get("x-forwarded-for")
    ip = (fwd.split(",")[0].strip() if fwd else request.client.host) if request.client else "unknown"
    return f"{ip}:{request.url.path}"


async def rate_limiter(request: Request):
    key = _client_key(request)
    now = time.monotonic()
    q = _buckets[key]
    # Select window/max per path if configured
    path = request.url.path
    win, mx = _WINDOW_SEC, _MAX_REQ
    cfg = _PER_PATH.get(path)
    if isinstance(cfg, list) and len(cfg) == 2:
        try:
            win = int(cfg[0]); mx = int(cfg[1])
        except Exception:
            pass

    # prune old
    while q and now - q[0] > win:
        q.popleft()
    if len(q) >= mx:
        raise HTTPException(status_code=429, detail="Too Many Requests")
    q.append(now)
