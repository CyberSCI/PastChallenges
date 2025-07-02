#!/bin/bash

set -euxo pipefail
cd terraform
tofu destroy -auto-approve
