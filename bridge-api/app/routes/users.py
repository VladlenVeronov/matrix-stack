"""User-related endpoints:

  POST /v1/matrix/users/sync     webhook from Supabase trigger
  GET  /v1/matrix/users/search   invite picker autocomplete (public)
"""
from __future__ import annotations

import structlog
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field

from app.deps import get_supabase, get_synapse, require_webhook_secret
from app.services.supabase_client import SupabaseClient
from app.services.synapse_admin import SynapseAdmin, make_localpart

router = APIRouter()
log = structlog.get_logger()


class UserSyncEvent(BaseModel):
    type: str = Field(pattern="^(UPDATE|DELETE)$")
    supabase_user_id: str
    username: str | None = None
    display_name: str | None = None
    avatar_url: str | None = None


@router.post("/users/sync", dependencies=[Depends(require_webhook_secret)])
async def users_sync(
    event: UserSyncEvent,
    syn: SynapseAdmin = Depends(get_synapse),
) -> dict:
    localpart = make_localpart(event.username, event.supabase_user_id)
    matrix_user_id = syn.matrix_id(localpart)

    if event.type == "DELETE":
        await syn.deactivate(matrix_user_id)
        log.info("matrix_user_deactivated", matrix_user_id=matrix_user_id)
        return {"status": "deactivated", "matrix_user_id": matrix_user_id}

    if event.type == "UPDATE":
        await syn.upsert_user(
            localpart,
            displayname=event.display_name or event.username or localpart,
            avatar_url=event.avatar_url,
        )
        log.info("matrix_user_updated", matrix_user_id=matrix_user_id)
        return {"status": "updated", "matrix_user_id": matrix_user_id}

    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="unknown_type")


@router.get("/users/search")
async def users_search(
    q: str = Query(..., min_length=2, max_length=64),
    limit: int = Query(10, ge=1, le=30),
    supa: SupabaseClient = Depends(get_supabase),
) -> list[dict]:
    """Public invite-picker autocomplete.

    Returns at most `limit` users whose username or email contains `q`
    AND who have already been provisioned in Matrix (matrix_user_id IS
    NOT NULL). The endpoint does not require auth — it leaks only
    public-by-design fields (username, display_name, avatar_url).
    """
    try:
        rows = await supa.search_users(q, limit=limit)
    except Exception as exc:  # pragma: no cover
        log.exception("users_search_failed", error=str(exc))
        return []
    return rows
