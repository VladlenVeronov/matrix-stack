# LiveKit — Traefik file-provider workaround

## Why this exists

Coolify's docker-provider auto-discovery does not register the LiveKit
container with Traefik, even with the correct labels in
`docker-compose.yml`:

```
traefik.enable=true
traefik.http.routers.https-0-...-livekit.rule=Host(`livekit.matrix.vir.group`)
traefik.http.routers.https-0-...-livekit.tls=true
traefik.http.routers.https-0-...-livekit.tls.certresolver=letsencrypt
traefik.http.services.https-0-...-livekit.loadbalancer.server.port=7880
traefik.docker.network=q50663r5jw52lfmbv86vb4i6
```

Traefik's docker-provider silently ignores them — no error in logs,
just no service registration. As a result every request to
`livekit.matrix.vir.group` returns 503 and Let's Encrypt never issues
a cert.

The cause is unclear; same labels work for `synapse`, `bridge-api`,
`synapse-admin`. Likely a quirk of the labels + docker-network name +
Traefik v3 docker provider in Coolify's specific setup.

## Workaround

Drop `livekit.yaml` directly into Traefik's file-provider directory.
Traefik watches it (`--providers.file.watch=true`) and applies the
route immediately, no restart needed.

```bash
scp livekit.yaml server:/tmp/
ssh server '
  cp /tmp/livekit.yaml /data/coolify/proxy/dynamic/livekit.yaml
  chmod 600 /data/coolify/proxy/dynamic/livekit.yaml
  chown 9999:root /data/coolify/proxy/dynamic/livekit.yaml
'
```

The cert is issued automatically on the first HTTPS request to the
domain.

## After every redeploy of matrix-stack

The container's IP on the Docker network may change. Verify with:

```bash
ssh server "docker inspect \
  \$(docker ps --format '{{.Names}}' | grep '^livekit-q50' | head -1) \
  --format '{{(index .NetworkSettings.Networks \"q50663r5jw52lfmbv86vb4i6\").IPAddress}}'"
```

If the printed IP differs from `10.0.3.3` in `livekit.yaml`, update the
file (Traefik picks the change up automatically).

## Long-term fix to investigate

- Move LiveKit out of Coolify-managed compose into its own standalone
  systemd-managed deployment, OR
- Use a DNS alias instead of IP (Traefik's docker provider uses the
  container name; the file provider doesn't, hence the IP).
- Element/Famedly devs report this is a known Traefik v3 + Docker
  rolling-deploy quirk where the new container's labels arrive before
  the old container's removal event, leaving the service definition
  in a half-applied state. Restarting the proxy normally fixes it but
  not in our case.
