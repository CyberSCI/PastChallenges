#!/bin/bash
set -e

: "${CYSPACE_DB_HOST:=db}"
: "${CYSPACE_DB_NAME:=cyspace}"
: "${CYSPACE_DB_USER:=cyspace}"
: "${CYSPACE_DB_PASS:=cyspace}"

echo "[entrypoint] waiting for database at ${CYSPACE_DB_HOST}..."
for i in $(seq 1 60); do
    if php -r "exit(@mysqli_connect(getenv('CYSPACE_DB_HOST'), getenv('CYSPACE_DB_USER'), getenv('CYSPACE_DB_PASS'), getenv('CYSPACE_DB_NAME')) ? 0 : 1);" >/dev/null 2>&1; then
        echo "[entrypoint] database is up."
        break
    fi
    sleep 1
    if [ "$i" = "60" ]; then
        echo "[entrypoint] database did not come up in time" >&2
        exit 1
    fi
done

echo "[entrypoint] seeding admin accounts..."
php /usr/local/share/cyspace/seed-admins.php || {
    echo "[entrypoint] admin seeding failed" >&2
    exit 1
}

echo "[entrypoint] starting $*"
exec "$@"
