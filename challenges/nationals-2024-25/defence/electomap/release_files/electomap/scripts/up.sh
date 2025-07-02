#!/bin/bash -e

set -euxo pipefail

docker compose --profile app up --build -d \
  && docker compose --profile app logs -f app mqtt
