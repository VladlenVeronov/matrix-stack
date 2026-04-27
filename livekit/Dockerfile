FROM livekit/livekit-server:v1.7

USER root
RUN apk add --no-cache gettext

COPY livekit.yaml.tmpl /etc/livekit/livekit.yaml.tmpl
COPY entrypoint.sh     /usr/local/bin/livekit-entrypoint
RUN chmod +x /usr/local/bin/livekit-entrypoint

ENTRYPOINT ["/usr/local/bin/livekit-entrypoint"]
