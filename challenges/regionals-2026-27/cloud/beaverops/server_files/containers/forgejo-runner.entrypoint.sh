#!/bin/sh

if [ -n "$DISABLE_RUNNER" ]; then
  tail -f /dev/null
fi

sleep 5
forgejo-runner daemon -c /data/runner-config.yml
