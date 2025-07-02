#!/bin/bash

set -euxo pipefail
mc alias set object-storage http://object-storage.badgescan.valverde.vote:9000 $ACCESS_KEY $SECRET_KEY 

mc mb --ignore-existing object-storage/static 
mc mb --ignore-existing object-storage/terraform
mc mb --ignore-existing object-storage/qr-codes

mc anonymous set download object-storage/qr-codes
mc anonymous set download object-storage/static
