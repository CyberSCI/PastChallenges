#!/bin/bash

set -euxo pipefail

pnpm run db:migrate
node build
