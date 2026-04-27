"""POST /v1/matrix/users/sync — webhook from Supabase.

Triggered by a `users` table AFTER UPDATE / AFTER DELETE database
trigger. The webhook keeps the Matrix profile in step with Supabase
without requiring the user to log into the app.
"""
from __future__ import annotations

import structlog
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from app.deps import get_synapse, require_webhook_secret
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
