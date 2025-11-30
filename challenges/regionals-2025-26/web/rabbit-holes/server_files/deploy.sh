#!/usr/bin/env bash

set -euxo pipefail

SERVER_ADDR="$1"

if [ -z "${SERVER_ADDR}" ]; then
  echo "Usage: ./deploy.sh <SERVER_ADDR>"
fi

git archive --format=tar HEAD > rabbit-holes.tar.gz
scp rabbit-holes.tar.gz "${SERVER_ADDR}:rabbit-holes.tar.gz"
