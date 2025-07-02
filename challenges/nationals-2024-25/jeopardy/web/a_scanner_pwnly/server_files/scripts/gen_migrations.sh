#!/bin/bash

set -euxo pipefail

MESSAGE=$1

cd terraform
export MAIN_DB_PASSWORD=$(jq -r ".main_db_password.value" secrets.json)
export MINIO_ACCESS_KEY=$(jq -r ".object_storage_user.value" secrets.json)
export MINIO_SECRET_KEY=$(jq -r ".object_storage_password.value" secrets.json)
cd ..
cd backend
export DATABASE_URL="postgresql+asyncpg://postgres:${MAIN_DB_PASSWORD}@localhost:5432/badgescan"
export MINIO_ENDPOINT="http://localhost:9000"
uv run alembic revision --autogenerate -m "$MESSAGE"
cd ..
