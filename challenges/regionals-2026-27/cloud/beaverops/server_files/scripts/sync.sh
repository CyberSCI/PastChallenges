#!/usr/bin/env bash

set -e

SCRIPT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" &>/dev/null && pwd)

CONTAINER_DIR=$(readlink -f "$SCRIPT_DIR/../containers")
CONFIG_DIR=$(readlink -f "$SCRIPT_DIR/../config")

for systemd_file in $(/bin/ls "$CONTAINER_DIR"); do
  ln -s --force "$CONTAINER_DIR/$systemd_file" /etc/containers/systemd
  echo "Synchronized $CONTAINER_DIR/$systemd_file"
done

cp "$CONFIG_DIR/forgejo/.env" /etc/containers/systemd/forgejo.env

mkdir -p /etc/containers/systemd/forgejo-data/.cache
cp -r $CONFIG_DIR/forgejo/data/* /etc/containers/systemd/forgejo-data
chown -R 1001:1001 /etc/containers/systemd/forgejo-data
chmod 775 /etc/containers/systemd/forgejo-data/.cache
chmod g+s /etc/containers/systemd/forgejo-data/.cache
