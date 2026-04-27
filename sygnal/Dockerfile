FROM matrixdotorg/sygnal:v0.17.0

USER root
RUN apt-get update \
 && apt-get install -y --no-install-recommends gettext-base \
 && rm -rf /var/lib/apt/lists/*

COPY sygnal.yaml.tmpl /etc/sygnal/sygnal.yaml.tmpl
COPY entrypoint.sh    /usr/local/bin/sygnal-entrypoint
RUN chmod +x /usr/local/bin/sygnal-entrypoint

# Upstream Sygnal image runs as user "sygnal" (uid varies — defer to image)
ENTRYPOINT ["/usr/local/bin/sygnal-entrypoint"]
