"""POST /v1/matrix/login — exchange a Supabase JWT for a Matrix token.

Flow:
    1. Client sends `Authorization: Bearer <supabase_jwt>`.
    2. We verify the JWT and read the user's row from `public.users`.
    3. Map `users.username` → Matrix localpart (canonical rule:
       Supabase = Mastodon = Matrix).
    4. Upsert the user in Synapse (idempotent).
    5. Persist `matrix_user_id` back to Supabase.
    6. Mint a fresh access_token via Admin masquerade and return it.

The Flutter client treats the response as a one-shot login — it stores
`access_token` and `device_id` in secure storage and uses them for the
duration of the device session.
"""
from __future__ import annotations

import structlog
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from app.config import Settings, get_settings
from app.deps import get_supabase, get_synapse, require_supabase_jwt
from app.services.supabase_client import SupabaseClient
from app.services.synapse_admin import SynapseAdmin, make_localpart

router = APIRouter()
log = structlog.get_logger()


class LoginResponse(BaseModel):
    user_id: str
    access_token: str
    device_id: str
    server_name: str
    homeserver_url: str


@router.post("/login", response_model=LoginResponse)
async def login(
    claims: dict = Depends(require_supabase_jwt),
    settings: Settings = Depends(get_settings),
    supa: SupabaseClient = Depends(get_supabase),
    syn: SynapseAdmin = Depends(get_synapse),
) -> LoginResponse:
    supabase_user_id = claims["sub"]

    profile = await supa.get_user_profile(supabase_user_id)
    if profile is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="supabase_profile_not_found",
        )

    localpart = make_localpart(profile.get("username"), supabase_user_id)
    displayname = (
        profile.get("display_name")
        or settings.default_displayname_template.format(
            username=profile.get("username") or localpart
        )
    )
    avatar = profile.get("avatar_url")

    matrix_user_id = await syn.upsert_user(
        localpart, displayname=displayname, avatar_url=avatar
    )
    access_token, device_id = await syn.mint_user_token(matrix_user_id)

    if profile.get("matrix_user_id") != matrix_user_id:
        await supa.patch_user_matrix_fields(
            supabase_user_id,
            matrix_user_id=matrix_user_id,
            matrix_device_id=device_id,
        )

    log.info(
        "matrix_login_ok",
        supabase_user_id=supabase_user_id,
        matrix_user_id=matrix_user_id,
        device_id=device_id,
    )

    return LoginResponse(
        user_id=matrix_user_id,
        access_token=access_token,
        device_id=device_id,
        server_name=settings.synapse_server_name,
        homeserver_url=settings.synapse_internal_url
        if settings.synapse_internal_url.startswith("https")
        else f"https://matrix.{settings.synapse_server_name}",
    )
