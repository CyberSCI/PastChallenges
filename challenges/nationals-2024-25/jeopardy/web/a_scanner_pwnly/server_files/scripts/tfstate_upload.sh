#!/bin/bash

set -euxo pipefail

mc alias set object-storage http://object-storage.badgescan.valverde.vote:9000 vvbs-admin $OBJECT_STORAGE_PASSWORD
# Just to make sure.
mc mb --ignore-existing object-storage/static 
mc mb --ignore-existing object-storage/terraform
mc mb --ignore-existing object-storage/qr-codes
mc put /terraform/terraform.tfstate object-storage/terraform/terraform.tfstate
