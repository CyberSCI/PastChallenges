#!/bin/bash

set -euxo pipefail

# [ W A R N I N G ]
# THIS SCRIPT WILL DELETE ALL DATA!
# DO NOT USE EXCEPT IN AN EMERGENCY!

docker compose --profile app down --volumes
