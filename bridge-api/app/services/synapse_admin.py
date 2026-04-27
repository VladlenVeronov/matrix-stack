"""Synapse Admin API client.

Reference: https://element-hq.github.io/synapse/latest/usage/administration/admin_api/index.html

We use three endpoints:
  - PUT  /_synapse/admin/v2/users/{user_id}      — create-or-update user
  - POST /_synapse/admin/v1/users/{user_id}/login — masquerade, mint token
  - POST /_synapse/admin/v1/deactivate/{user_id} — soft-delete on user wipe
"""
from __future__ import annotations

import re

import httpx
from fastapi import HTTPException, status

from app.config import Settings


_LOCALPART_RE = re.compile(r"[^a-z0-9._=\-/]")


def make_localpart(username: str | None, fallback_uuid: str) -> str:
    """Map a Supabase username to a Matrix localpart (the bit before `:`).

    Matrix spec only allows `[a-z0-9._=\\-/]`. Anything else is replaced.
    Empty / missing usernames fall back to `u_<short-uuid>`.
    """
    raw = (username or "").strip().lower()
    safe = _LOCALPART_RE.sub("_", raw)
    if not safe or len(safe) < 3:
        return f"u_{fallback_uuid.replace('-', '')[:12]}"
    return safe[:64]


class SynapseAdmin:
    def __init__(self, settings: Settings, client: httpx.AsyncClient) -> None:
        self._base = settings.synapse_internal_url.rstrip("/")
        self._server_name = settings.synapse_server_name
        self._client = client
        self._headers = {
            "Authorization": f"Bearer {settings.synapse_admin_token}",
            "Content-Type": "application/json",
        }

    def matrix_id(self, localpart: str) -> str:
        return f"@{localpart}:{self._server_name}"

    async def upsert_user(
        self,
        localpart: str,
        *,
        displayname: str | None = None,
        avatar_url: str | None = None,
        deactivated: bool = False,
    ) -> str:
        """Create or update a user. Returns the full Matrix ID.

        We do NOT set a password — Synapse rejects password writes when
        password_config.enabled is false. Login happens exclusively via
        admin masquerade, so the password slot stays empty.
        """
        user_id = self.matrix_id(localpart)
        url = f"{self._base}/_synapse/admin/v2/users/{user_id}"
        body: dict = {
            "deactivated": deactivated,
            "admin": False,
        }
        if displayname is not None:
            body["displayname"] = displayname
        if avatar_url is not None:
            body["avatar_url"] = avatar_url

        r = await self._client.put(url, headers=self._headers, json=body)
        if r.status_code not in (200, 201):
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"synapse_upsert_failed: {r.status_code} {r.text[:200]}",
            )
        return user_id

    async def mint_user_token(self, user_id: str) -> tuple[str, str]:
        """Admin masquerade — get an access token + device id for a user."""
        url = f"{self._base}/_synapse/admin/v1/users/{user_id}/login"
        r = await self._client.post(url, headers=self._headers, json={})
        if r.status_code != 200:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"synapse_mint_token_failed: {r.status_code} {r.text[:200]}",
            )
        data = r.json()
        # Synapse returns { access_token, ... }; device_id is auto-generated
        return data["access_token"], data.get("device_id", "")

    async def deactivate(self, user_id: str) -> None:
        url = f"{self._base}/_synapse/admin/v1/deactivate/{user_id}"
        r = await self._client.post(
            url,
            headers=self._headers,
            json={"erase": True},
        )
        if r.status_code != 200:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"synapse_deactivate_failed: {r.status_code} {r.text[:200]}",
            )
