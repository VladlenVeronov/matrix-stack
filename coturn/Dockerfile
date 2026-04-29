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

# Run as root: 3478 is a privileged port, and the upstream image
# doesn't ship a non-root user we can fall back to. We're sandboxed
# in a container with no caps beyond what coturn needs anyway.
ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]
