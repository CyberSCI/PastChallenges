#!/bin/bash
set -e

echo "[entrypoint] Disabling ASLR …"
echo 0 > /proc/sys/kernel/randomize_va_space || echo "[entrypoint] WARNING: could not disable ASLR (need --privileged)"

unset FLAG

echo "[entrypoint] Starting Dead Air relay service on :5000 …"
exec python3 /app/app.py
