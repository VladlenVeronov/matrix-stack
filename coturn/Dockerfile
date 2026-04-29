# =============================================================
# coturn — TURN/STUN server for Matrix 1:1 calls
# Alpine base; envsubst comes from gettext.
# =============================================================
FROM coturn/coturn:4.6.2-alpine

USER root
RUN apk add --no-cache gettext bash

COPY turnserver.conf.tmpl /etc/coturn/turnserver.conf.tmpl
COPY entrypoint.sh        /usr/local/bin/entrypoint.sh
RUN chmod +x /usr/local/bin/entrypoint.sh

# Run as the non-root coturn user baked into the upstream image.
USER coturn

ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]
