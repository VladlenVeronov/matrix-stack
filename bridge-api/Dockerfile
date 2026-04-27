# =============================================================
# bridge-api — FastAPI service mediating Supabase ↔ Matrix
# Multi-stage build keeps the runtime image ~80 MB.
# =============================================================

FROM python:3.12-slim AS builder

WORKDIR /build
RUN apt-get update \
 && apt-get install -y --no-install-recommends build-essential \
 && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt

# -------------------------------------------------------------
FROM python:3.12-slim AS runtime

LABEL org.opencontainers.image.source="https://github.com/VladlenVeronov/matrix-stack"
LABEL org.opencontainers.image.description="Supabase ↔ Matrix bridge for VIR.GROUP"

# Non-root user
RUN useradd --create-home --shell /usr/sbin/nologin --uid 1001 bridge

WORKDIR /app
COPY --from=builder /root/.local /home/bridge/.local
COPY --chown=bridge:bridge app/ ./app/

ENV PATH=/home/bridge/.local/bin:$PATH \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

USER bridge
EXPOSE 8000

HEALTHCHECK --interval=15s --timeout=5s --retries=5 \
  CMD python -c "import urllib.request,sys; r=urllib.request.urlopen('http://127.0.0.1:8000/v1/matrix/health',timeout=3); sys.exit(0 if r.status==200 else 1)"

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2", "--proxy-headers", "--forwarded-allow-ips", "*"]
