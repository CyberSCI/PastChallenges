# syntax=docker/dockerfile:1

FROM debian:12-slim

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y --no-install-recommends \
        nginx \
        python3 \
        python3-pip \
        python3-pil \
        python3-flask \
        python3-waitress \
        supervisor \
        fonts-dejavu-core \
        ca-certificates \
    && pip install --no-cache-dir --break-system-packages ariadne \
    && rm -rf /var/lib/apt/lists/* \
    && mkdir -p /var/log/supervisor

# Service configs
COPY docker/nginx.conf /etc/nginx/sites-available/default
COPY docker/supervisord.conf /etc/supervisor/conf.d/ocr-rotator.conf

# Application code
COPY src/generator/generator.py /usr/local/bin/generator.py
COPY src/api/app.py /usr/local/bin/api.py
RUN chmod 755 /usr/local/bin/generator.py /usr/local/bin/api.py

# Static frontend (QuoteVault site)
COPY src/site/ /var/www/site/

# PoW proxy
COPY src/pow-server/pow_server.py /usr/local/bin/pow_server.py
RUN chmod 755 /usr/local/bin/pow_server.py

# Disable any other nginx default
RUN rm -f /etc/nginx/sites-enabled/default \
    && ln -sf /etc/nginx/sites-available/default /etc/nginx/sites-enabled/default

# Unprivileged user for the api + generator processes.
RUN useradd -m -s /bin/sh -u 1000 ocr-rotator

# Entrypoint
COPY docker/entrypoint.sh /entrypoint.sh
RUN chmod 755 /entrypoint.sh

EXPOSE 8080

ENTRYPOINT ["/entrypoint.sh"]
