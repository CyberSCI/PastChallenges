# Use minimal Debian slim base image
FROM debian:bullseye-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    python-is-python3 \
    gunicorn \
    cron \
    unzip \
    mono-complete \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

COPY webapp/ /app/webapp/
RUN pip3 install --no-cache-dir -r webapp/requirements.txt
COPY history_stealer/ /app/history_stealer/
# Copy flag.txt to /root
COPY flag.txt /root/flag.txt

# Rely on app.py to create directories
# Volume mounts will handle persistence
RUN chmod -R 777 /app/webapp/uploads /app/webapp/unzipped /app/webapp/static/builds 2>/dev/null || true

RUN echo "* * * * * root echo \"Uptime: \$(uptime)\" >> /var/log/cron.log 2>&1" > /etc/cron.d/crontab_job \
    && chmod 0644 /etc/cron.d/crontab_job \
    && crontab /etc/cron.d/crontab_job

ENV PYTHONPATH=/app/webapp
ENV SCRIPT_NAME=/ba5e864526cbaa667bca74e2d1d453f0

CMD service cron start && gunicorn --bind 0.0.0.0:49858 --workers 3 --user root --group root webapp.app:app
