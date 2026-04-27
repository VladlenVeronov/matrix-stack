# bridge-api

FastAPI service mediating between **Supabase** and **Synapse**.

The Flutter app authenticates with Supabase as usual. To talk to Matrix,
it sends its Supabase JWT here and gets back a Matrix access token —
the user never sees a separate Matrix login.

## Endpoints

| Method | Path                    | Auth                         | Purpose                                      |
| ------ | ----------------------- | ---------------------------- | -------------------------------------------- |
| GET    | `/v1/matrix/health`     | none                         | liveness                                     |
| POST   | `/v1/matrix/login`      | Bearer Supabase JWT          | exchange JWT → Matrix `access_token`         |
| POST   | `/v1/matrix/users/sync` | `X-Webhook-Signature` header | Supabase trigger → keep Matrix profile in step|
| GET    | `/v1/matrix/docs`       | none                         | OpenAPI / Swagger UI                         |

## Username mapping rule

Canonical: **Supabase `users.username` = Matrix localpart = Mastodon username.**

`make_localpart()` strips characters Matrix doesn't permit (only
`[a-z0-9._=\-/]` allowed) and falls back to `u_<short-uuid>` if the
username is missing or shorter than 3 chars.

## Local development

```bash
cd bridge-api
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

export BRIDGE_SUPABASE_URL=https://xxxxxx.supabase.co
export BRIDGE_SUPABASE_JWT_SECRET=...
export BRIDGE_SUPABASE_SERVICE_ROLE=...
export BRIDGE_SYNAPSE_INTERNAL_URL=http://localhost:8008
export BRIDGE_SYNAPSE_SERVER_NAME=vir.group
export BRIDGE_SYNAPSE_ADMIN_TOKEN=...

uvicorn app.main:app --reload --port 8000
```

Swagger UI at <http://localhost:8000/v1/matrix/docs>.

## Required Supabase schema additions

Add two columns to `public.users` (migration lives in `vir-supabase`):

```sql
alter table public.users add column if not exists matrix_user_id   text;
alter table public.users add column if not exists matrix_device_id text;
```

The bridge writes both via the Supabase REST API using the service-role
key; RLS does not apply.
