"""Synapse Admin API client.

Reference: https://element-hq.github.io/synapse/latest/usage/administration/admin_api/index.html

We use these endpoints:
  - PUT  /_synapse/admin/v2/users/{user_id}      — create-or-update user (sets password)
  - POST /_matrix/client/v3/login                — password login (gives device-bound token, required for E2EE)
  - POST /_synapse/admin/v1/deactivate/{user_id} — soft-delete on user wipe

Note on E2EE:
  The `admin/v1/users/{userId}/login` masquerade endpoint returns a token
  WITHOUT a device_id, which causes /keys/upload to reject E2EE bootstrap
  with "To upload keys, you must pass device_id when authenticating". So
  for E2EE-capable sessions we go through the standard `/login` flow
  with `m.login.password`, where Synapse mints both an access_token and
  a fresh device_id.

The user's password is derived as `HMAC-SHA256(BRIDGE_USER_PASSWORD_SECRET,
matrix_user_id)` — fully deterministic from the Synapse mxid, no extra
storage in bridge or Supabase, but reproducible only by code that holds
the env-secret.
"""
from __future__ import annotations

import hashlib
import hmac
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
        # Falls back to the admin token if the dedicated secret isn't set in
        # env yet — sufficient entropy for our threat model.
        self._password_secret = (
            getattr(settings, "user_password_secret", None)
            or settings.synapse_admin_token
        ).encode("utf-8")

    def matrix_id(self, localpart: str) -> str:
        return f"@{localpart}:{self._server_name}"

    def _user_password(self, user_id: str) -> str:
        return hmac.new(
            self._password_secret,
            user_id.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()

    async def upsert_user(
        self,
        localpart: str,
        *,
        displayname: str | None = None,
        avatar_url: str | None = None,
        deactivated: bool = False,
    ) -> str:
        """Create or update a user. Returns the full Matrix ID.

        Sets the user's password to a deterministic HMAC of the user_id.
        Synapse must have password_config.enabled=true for the subsequent
        /login to work.
        """
        user_id = self.matrix_id(localpart)
        password = self._user_password(user_id)
        url = f"{self._base}/_synapse/admin/v2/users/{user_id}"
        body: dict = {
            "deactivated": deactivated,
            "admin": False,
            "password": password,
        }
        if displayname is not None:
            body["displayname"] = displayname
        # Only forward `avatar_url` if it's a Matrix-native mxc:// reference.
        # Synapse stores whatever we send, but the matrix-dart-sdk parser
        # (`ProfileInformation.fromJson`) refuses anything that isn't
        # `mxc://...` and crashes the room user-profile fetch with
        # "Uri not an mxc URI". Foreign HTTP avatars (Mastodon CDN, etc.)
        # need to be re-hosted via /upload first; until that's wired up,
        # silently drop them so the chat keeps working.
        if avatar_url is not None and avatar_url.startswith("mxc://"):
            body["avatar_url"] = avatar_url

        r = await self._client.put(url, headers=self._headers, json=body)
        if r.status_code not in (200, 201):
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"synapse_upsert_failed: {r.status_code} {r.text[:200]}",
            )
        return user_id

    async def mint_user_token(self, user_id: str) -> tuple[str, str]:
        """Login as the user via the public /v3/login endpoint with the
        deterministic per-user password. Returns (access_token, device_id).

        We do NOT use /_synapse/admin/v1/users/{userId}/login here because
        that endpoint returns a token without a device_id, which breaks
        E2EE bootstrap on the client (POST /keys/upload rejected with
        "To upload keys, you must pass device_id when authenticating").
        """
        password = self._user_password(user_id)
        url = f"{self._base}/_matrix/client/v3/login"
        body = {
            "type": "m.login.password",
            "identifier": {"type": "m.id.user", "user": user_id},
            "password": password,
            "initial_device_display_name": "vir.group",
        }
        r = await self._client.post(url, json=body)
        if r.status_code != 200:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"synapse_mint_token_failed: {r.status_code} {r.text[:200]}",
            )
        data = r.json()
        access_token = data.get("access_token")
        device_id = data.get("device_id")
        if not access_token or not device_id:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"synapse_mint_token_incomplete: {data}",
            )
        return access_token, device_id

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
