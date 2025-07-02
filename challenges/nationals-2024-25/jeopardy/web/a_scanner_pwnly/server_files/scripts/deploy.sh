#!/bin/bash

set -euxo pipefail

docker pull postgres:14
docker pull quay.io/minio/minio
docker pull quay.io/minio/mc

cd terraform
tofu init -upgrade
tofu validate
tofu apply -auto-approve
tofu output -show-sensitive -json > secrets.json
export OBJECT_STORAGE_PASSWORD=$(jq -r ".object_storage_password.value" secrets.json)
cd ..
sleep 5
docker run \
  --rm \
  --name tfstate-upload \
  --mount type=bind,src="$PWD/terraform/terraform.tfstate",dst=/terraform/terraform.tfstate \
  --mount type=bind,src="$PWD/scripts/tfstate_upload.sh",dst=/scripts/tfstate_upload.sh \
  --network vvbs-network \
  -e "OBJECT_STORAGE_PASSWORD=$OBJECT_STORAGE_PASSWORD" \
  --entrypoint /scripts/tfstate_upload.sh \
  minio/mc 
docker logs vvbs-backend -f
