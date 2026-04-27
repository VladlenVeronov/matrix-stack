FROM python:3.11-slim AS builder
RUN pip install --no-cache-dir --user matrix-sygnal==0.15.1

FROM python:3.11-slim
RUN apt-get update \
 && apt-get install -y --no-install-recommends gettext-base \
 && rm -rf /var/lib/apt/lists/*

RUN useradd --create-home --shell /usr/sbin/nologin --uid 991 sygnal
COPY --from=builder --chown=sygnal:sygnal /root/.local /home/sygnal/.local
COPY sygnal.yaml.tmpl /etc/sygnal/sygnal.yaml.tmpl
COPY entrypoint.sh    /usr/local/bin/sygnal-entrypoint
RUN chmod +x /usr/local/bin/sygnal-entrypoint

USER sygnal
ENV PATH=/home/sygnal/.local/bin:$PATH \
    PYTHONUNBUFFERED=1
EXPOSE 5000
ENTRYPOINT ["/usr/local/bin/sygnal-entrypoint"]
