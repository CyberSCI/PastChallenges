#!/usr/bin/env bash

set -x

systemctl stop forgejo.service \
  forgejo-runner.service \
  forgejo-db.service \
  forgejo-podman-runtime.service

podman volume ls | awk 'NR>1{print $2}' | xargs podman volume rm
