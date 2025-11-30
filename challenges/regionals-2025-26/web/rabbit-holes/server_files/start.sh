#!/bin/bash
set -euxo pipefail

docker rm -f rabbit_holes
docker build -t rabbit-holes:latest .
docker run -p "13370:13370" -d --name rabbit_holes --restart unless-stopped rabbit-holes:latest
