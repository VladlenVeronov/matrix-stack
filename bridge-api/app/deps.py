"""FastAPI dependencies — shared httpx client, settings, auth guards."""
from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import httpx
from fastapi import Depends, Header, HTTPException, status

from app.config import Settings, get_settings
from app.services.supabase_client import SupabaseClient
from app.services.supabase_jwt import verify_supabase_jwt
from app.services.synapse_admin import SynapseAdmin


_client: httpx.AsyncClient | None = None


@asynccontextmanager
async def lifespan_http_client() -> AsyncIterator[httpx.AsyncClient]:
    global _client
    _client = httpx.AsyncClient(timeout=httpx.Timeout(15.0))
    try:
        yield _client
    finally:
        await _client.aclose()
        _client = None


def get_http() -> httpx.AsyncClient:
    if _client is None:
        # Cold-start path: build a per-request client. Slow but correct.
        return httpx.AsyncClient(timeout=httpx.Timeout(15.0))
    return _client


def get_synapse(
    settings: Settings = Depends(get_settings),
    http: httpx.AsyncClient = Depends(get_http),
) -> SynapseAdmin:
    return SynapseAdmin(settings, http)


def get_supabase(
    settings: Settings = Depends(get_settings),
    http: httpx.AsyncClient = Depends(get_http),
) -> SupabaseClient:
    return SupabaseClient(settings, http)


def require_supabase_jwt(
    authorization: str | None = Header(default=None),
    settings: Settings = Depends(get_settings),
) -> dict:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="missing_bearer_token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    token = authorization.split(" ", 1)[1].strip()
    return verify_supabase_jwt(token, settings)


def require_webhook_secret(
    x_webhook_signature: str | None = Header(default=None),
    settings: Settings = Depends(get_settings),
) -> None:
    if not settings.webhook_secret:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="webhook_disabled",
        )
    if not x_webhook_signature or x_webhook_signature != settings.webhook_secret:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="invalid_webhook_signature",
        )
