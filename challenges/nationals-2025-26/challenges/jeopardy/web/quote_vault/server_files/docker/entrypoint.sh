#!/bin/sh
set -e

# /data is a tmpfs mount in docker-compose; reset perms so the unprivileged
# user can write into it.
mkdir -p /data
chown ocr-rotator:ocr-rotator /data
chmod 755 /data

# nginx serves /data/current/images. Until the generator's first cycle finishes,
# /data/current is missing — nginx will return 404, which is fine.

exec /usr/bin/supervisord -n -c /etc/supervisor/supervisord.conf
