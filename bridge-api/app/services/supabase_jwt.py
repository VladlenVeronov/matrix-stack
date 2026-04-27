"""Supabase JWT verification.

Supabase issues HS256-signed access tokens. The shared secret lives in
the Supabase dashboard under Project Settings → API → JWT Secret. We
validate signature, expiry and audience here, then return the decoded
claims for downstream use.
"""
from __future__ import annotations

import jwt
from fastapi import HTTPException, status

from app.config import Settings


class SupabaseJWTError(HTTPException):
    def __init__(self, detail: str) -> None:
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
            headers={"WWW-Authenticate": "Bearer"},
        )


def verify_supabase_jwt(token: str, settings: Settings) -> dict:
    """Verify a Supabase access token and return its claims.

    Raises HTTPException 401 on any validation failure.
    """
    try:
        claims = jwt.decode(
            token,
            settings.supabase_jwt_secret,
            algorithms=["HS256"],
            audience="authenticated",
            options={"require": ["sub", "exp", "aud"]},
        )
    except jwt.ExpiredSignatureError as exc:
        raise SupabaseJWTError("token_expired") from exc
    except jwt.InvalidAudienceError as exc:
        raise SupabaseJWTError("invalid_audience") from exc
    except jwt.InvalidSignatureError as exc:
        raise SupabaseJWTError("invalid_signature") from exc
    except jwt.PyJWTError as exc:
        raise SupabaseJWTError("invalid_token") from exc

    if claims.get("role") not in {"authenticated", "service_role"}:
        raise SupabaseJWTError("forbidden_role")

    return claims
