FROM matrixdotorg/sygnal:v0.15.1

USER root
RUN apk add --no-cache gettext

COPY sygnal.yaml.tmpl /etc/sygnal/sygnal.yaml.tmpl
COPY entrypoint.sh    /usr/local/bin/sygnal-entrypoint
RUN chmod +x /usr/local/bin/sygnal-entrypoint

USER 991
ENTRYPOINT ["/usr/local/bin/sygnal-entrypoint"]
