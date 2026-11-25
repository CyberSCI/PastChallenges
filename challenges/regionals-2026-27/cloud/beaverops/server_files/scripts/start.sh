#!/usr/bin/env bash

SCRIPT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" &>/dev/null && pwd)

"$SCRIPT_DIR/sync.sh"

echo "Starting services..."

systemctl daemon-reload
# systemctl start verdaccio.service
systemctl start forgejo.service && echo "ForgeJo service started."
systemctl start forgejo-runner.service && echo "ForgeJo runner service started."
