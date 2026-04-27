# Synapse with our custom entrypoint that templates homeserver.yaml.
FROM matrixdotorg/synapse:v1.116.0

# envsubst lives in gettext-base
RUN apt-get update \
 && apt-get install -y --no-install-recommends gettext-base \
 && rm -rf /var/lib/apt/lists/*

COPY homeserver.yaml.tmpl /etc/matrix-synapse/homeserver.yaml.tmpl
COPY log.config            /etc/matrix-synapse/log.config
COPY entrypoint.sh         /usr/local/bin/matrix-stack-entrypoint
RUN chmod +x /usr/local/bin/matrix-stack-entrypoint

ENTRYPOINT ["/usr/local/bin/matrix-stack-entrypoint"]
