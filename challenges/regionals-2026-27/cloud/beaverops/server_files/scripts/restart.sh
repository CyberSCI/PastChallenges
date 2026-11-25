#!/usr/bin/env bash

SCRIPT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" &>/dev/null && pwd)

"$SCRIPT_DIR/sync.sh"

echo "Starting services..."

systemctl daemon-reload
systemctl restart forgejo.service && echo "ForgeJo service restarted."
systemctl restart forgejo-runner.service && echo "ForgeJo runner service restarted."
