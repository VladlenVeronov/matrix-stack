"""Thin Supabase REST client used by the bridge.

We only need a handful of operations against the `users` and `auth.users`
tables, so a full SDK would be overkill. All requests use the service
role key and therefore bypass RLS.
"""
from __future__ import annotations

import httpx

from app.config import Settings


class SupabaseClient:
    def __init__(self, settings: Settings, client: httpx.AsyncClient) -> None:
        self._url = str(settings.supabase_url).rstrip("/")
        self._client = client
        self._headers = {
            "apikey": settings.supabase_service_role,
            "Authorization": f"Bearer {settings.supabase_service_role}",
            "Content-Type": "application/json",
            # Some Supabase projects default to a non-public schema (e.g. 'api');
            # force public so we always hit public.users regardless of project config.
            "Accept-Profile": "public",
            "Content-Profile": "public",
        }

    async def get_user_profile(self, user_id: str) -> dict | None:
        """Fetch one row from public.users by id (UUID)."""
        url = f"{self._url}/rest/v1/users"
        params = {"id": f"eq.{user_id}", "select": "*", "limit": "1"}
        r = await self._client.get(url, params=params, headers=self._headers)
        r.raise_for_status()
        rows = r.json()
        return rows[0] if rows else None

    async def search_users(self, query: str, limit: int = 10) -> list[dict]:
        """Username/display-name fuzzy search for the invite picker.

        Looks up rows in public.users where username OR email contains
        the query (case-insensitive). Only returns rows that have a
        matrix_user_id — otherwise the row can't be invited yet.
        """
        url = f"{self._url}/rest/v1/users"
        params = {
            "select": "username,display_name,avatar_url,matrix_user_id",
            "or": f"(username.ilike.%{query}%,email.ilike.%{query}%)",
            "matrix_user_id": "not.is.null",
            "limit": str(limit),
        }
        r = await self._client.get(url, params=params, headers=self._headers)
        r.raise_for_status()
        return list(r.json())

    async def patch_user_matrix_fields(
        self,
        user_id: str,
        *,
        matrix_user_id: str,
        matrix_device_id: str | None = None,
    ) -> None:
        """Persist Matrix identity into public.users."""
        url = f"{self._url}/rest/v1/users"
        params = {"id": f"eq.{user_id}"}
        body: dict = {"matrix_user_id": matrix_user_id}
        if matrix_device_id:
            body["matrix_device_id"] = matrix_device_id
        r = await self._client.patch(
            url,
            params=params,
            headers={**self._headers, "Prefer": "return=minimal"},
            json=body,
        )
        r.raise_for_status()
