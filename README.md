# matrix-stack

Production-grade self-hosted Matrix/Synapse stack for **VIR.GROUP**.

End-to-end encrypted chat, voice and video, replacing the previous
Supabase-backed pseudo-messenger inside the Flutter app.

## Status — Phase 1a (foundation)

This commit ships the **homeserver foundation only**:

| Component       | Image                                  | Purpose                                |
| --------------- | -------------------------------------- | -------------------------------------- |
| Synapse         | `matrixdotorg/synapse:v1.116.0`        | Matrix homeserver                      |
| Postgres        | `postgres:16-alpine`                   | Synapse database (NOT Supabase)        |
| Redis           | `redis:7-alpine`                       | replication / presence cache           |
| Synapse-Admin   | `awesometechnologies/synapse-admin`    | web UI for moderation                  |

Following phases (separate commits):

- **1b** — `bridge-api` (Supabase JWT → Matrix login, user provisioning)
- **1c** — Sygnal (push gateway: FCM v1 + APNs)
- **1d** — LiveKit + Element Call (group voice/video)
- **1e** — `.well-known/matrix/*` static delegation files

## Architecture

```
Flutter app (vir-supabase / lib/matrix/)
        │
        │ 1) login: POST bridge.vir.group/v1/matrix/login   (Supabase JWT)
        │    ──► access_token
        │
        │ 2) sync / send / E2EE:  matrix.vir.group  (Client-Server API)
        ▼
┌────────────────────────────────────────────────────────────────┐
│  Coolify  (server 168.231.108.21)                               │
│                                                                 │
│   matrix.vir.group  ────►  Synapse  ──►  postgres-matrix         │
│                                     ──►  redis-matrix            │
│                                     ──►  /data/media_store       │
│                                                                 │
│   bridge.vir.group  ────►  bridge-api  (FastAPI, Phase 1b)      │
│   admin.matrix.vir.group ► Synapse-Admin SPA                    │
│   livekit.matrix.vir.group ► LiveKit SFU (Phase 1d)             │
└────────────────────────────────────────────────────────────────┘
```

The bridge sits between Supabase and Synapse: a Flutter client never
talks to the Synapse Admin API directly. It calls the bridge with its
Supabase JWT and gets back a Matrix access token; the bridge keeps the
two user identities in sync (`username`, `display_name`, `avatar_url`).

## Local development

```bash
git clone https://github.com/VladlenVeronov/matrix-stack
cd matrix-stack

cp .env.example .env
./scripts/gen_secrets.sh

docker compose up -d postgres-matrix redis-matrix
docker compose up --build synapse
```

The first run generates `signing.key` automatically. The container is
healthy when `curl http://localhost:8008/health` returns `OK`.

To create the admin user (only the first time):

```bash
./scripts/init_admin_user.sh admin <strong-password>
```

## Production deploy via Coolify

1. **DNS** — three records, **DNS-only (gray cloud)** in Cloudflare:
   ```
   matrix.vir.group         → 168.231.108.21
   bridge.vir.group         → 168.231.108.21
   admin.matrix.vir.group   → 168.231.108.21
   ```

2. **New Coolify resource** → Application → Public Repository →
   `https://github.com/VladlenVeronov/matrix-stack` → Build pack:
   *Docker Compose*.

3. **Environment Variables** — paste contents of your generated `.env`
   (run `./scripts/gen_secrets.sh` locally first).

4. **Domains** — map in Coolify:
   - `matrix.vir.group`        → service `synapse`,        port `8008`
   - `admin.matrix.vir.group`  → service `synapse-admin`,  port `80`

5. **Persistent storage** — three named volumes: `synapse-data`,
   `postgres-matrix-data`, `redis-matrix-data`.

6. **Deploy**, wait for health checks to pass, then:
   ```bash
   ssh server 'docker exec -it synapse register_new_matrix_user \
     -c /data/homeserver.yaml -u admin -p <pass> -a http://localhost:8008'
   ```

7. **Smoke test**:
   ```bash
   curl https://matrix.vir.group/_matrix/client/versions
   # → {"versions": ["v1.1", ..., "v1.11"], ...}
   ```

## Security defaults

- `enable_registration: false` — public sign-up is **off**; the bridge
  provisions users using the registration shared secret.
- `password_config.enabled: false` — Matrix-native password login is
  **off**; the only path to a token is via the bridge.
- `federation_domain_whitelist: []` — federation **off**; the homeserver
  does not exchange events with the public Matrix network.
- `encryption_enabled_by_default_for_room_type: all` — every newly
  created room is **E2EE-encrypted**.
- `allow_guest_access: false` — no anonymous read access.

These defaults make the homeserver a closed business messenger from
day one. They can be relaxed later (e.g. enabling federation against a
whitelist of partner servers) without rebuilding state.

## What this repo deliberately does **not** do

- It does **not** include Caddy. Coolify's built-in proxy handles TLS
  termination on the three domains above.
- It does **not** ship secrets. `.env` is `.gitignore`'d; production
  secrets live in Coolify's encrypted env store.
- It does **not** open federation ports (8448). If federation is ever
  enabled, that is a separate change.
