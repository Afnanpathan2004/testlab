"""Lightweight security helpers: CSRF token and per-session rate limiter."""
from __future__ import annotations

import secrets
import time
from dataclasses import dataclass
from typing import Dict

import streamlit as st

from config.settings import settings


CSRF_KEY = "_csrf_token"
RL_BUCKET_KEY = "_rate_limiter_buckets"


def get_csrf_token() -> str:
    token = st.session_state.get(CSRF_KEY)
    if not token:
        token = secrets.token_urlsafe(16)
        st.session_state[CSRF_KEY] = token
    return token


def verify_csrf_token(token: str) -> bool:
    return bool(token and st.session_state.get(CSRF_KEY) == token)


@dataclass
class RateBucket:
    count: int
    reset_at: float


def _get_buckets() -> Dict[str, RateBucket]:
    if RL_BUCKET_KEY not in st.session_state:
        st.session_state[RL_BUCKET_KEY] = {}
    return st.session_state[RL_BUCKET_KEY]


def allow_action(key: str, limit_per_minute: int | None = None) -> bool:
    """Simple token bucket per session for rate limiting UI actions."""
    limit = limit_per_minute or settings.rate_limit_per_minute
    now = time.time()
    buckets = _get_buckets()
    b = buckets.get(key)
    if not b or now >= b.reset_at:
        b = RateBucket(count=0, reset_at=now + 60)
        buckets[key] = b
    if b.count >= limit:
        return False
    b.count += 1
    return True
