import logging

import structlog
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.requests import Request

from app.config import get_settings
from app.routes import health, login, users

settings = get_settings()

logging.basicConfig(level=settings.log_level)
structlog.configure(
    processors=[
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer(),
    ],
    wrapper_class=structlog.make_filtering_bound_logger(
        getattr(logging, settings.log_level.upper(), logging.INFO)
    ),
)
log = structlog.get_logger()

app = FastAPI(
    title="VIR.GROUP — Matrix Bridge API",
    version="0.1.0",
    docs_url="/v1/matrix/docs",
    redoc_url=None,
    openapi_url="/v1/matrix/openapi.json",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["Authorization", "Content-Type", "X-Webhook-Signature"],
)

app.include_router(health.router, prefix="/v1/matrix", tags=["health"])
app.include_router(login.router, prefix="/v1/matrix", tags=["auth"])
app.include_router(users.router, prefix="/v1/matrix", tags=["users"])


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    log.exception("unhandled_exception", path=request.url.path, error=str(exc))
    return JSONResponse(status_code=500, content={"error": "internal_server_error"})
