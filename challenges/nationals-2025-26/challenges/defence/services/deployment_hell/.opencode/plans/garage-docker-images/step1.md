# Step 1: Garage Configuration

## `garage/garage.toml`

Currently empty. Write full single-node config:

```toml
metadata_dir = "/var/lib/garage/meta"
data_dir = "/var/lib/garage/data"
db_engine = "lmdb"

replication_factor = 1

[s3_api]
s3_region = "garage"
api_bind_addr = "[::]:3900"
root_domain = ".s3.garage.localhost"

[s3_web]
bind_addr = "[::]:3901"
root_domain = ".web.garage.localhost"

[admin]
api_bind_addr = "[::]:3902"

[rpc]
bind_addr = "[::]:3901"
secret_file = "/var/lib/garage/meta/rpc_secret"
```

Note: `replication_factor = 1` since single node.

## `garage/init.sh`

Bootstrap script to run after Garage is up. Handles:
1. Wait for Garage admin API (port 3902) to be ready
2. Get node ID, assign layout, apply layout
3. Create API key
4. Create `docker-images` bucket
5. Grant key full access to bucket
6. Write credentials to a shared file Jenkins can read

```bash
#!/bin/bash
set -euo pipefail

GARAGE_ADMIN="http://garage:3902"

# Wait for garage
until curl -sf "$GARAGE_ADMIN/v1/health" > /dev/null 2>&1; do
  echo "Waiting for Garage..."
  sleep 2
done

# Get node ID and assign layout
NODE_ID=$(curl -sf "$GARAGE_ADMIN/v1/status" | jq -r '.node')
curl -sf -X POST "$GARAGE_ADMIN/v1/layout" \
  -H "Content-Type: application/json" \
  -d "[{\"id\": \"$NODE_ID\", \"zone\": \"dc1\", \"capacity\": 1073741824}]"
curl -sf -X POST "$GARAGE_ADMIN/v1/layout/apply" \
  -H "Content-Type: application/json" \
  -d '{"version": 1}'

# Create key
KEY_JSON=$(curl -sf -X POST "$GARAGE_ADMIN/v1/key" \
  -H "Content-Type: application/json" \
  -d '{"name": "jenkins"}')
ACCESS_KEY=$(echo "$KEY_JSON" | jq -r '.accessKeyId')
SECRET_KEY=$(echo "$KEY_JSON" | jq -r '.secretAccessKey')

# Create bucket and grant access
BUCKET_JSON=$(curl -sf -X POST "$GARAGE_ADMIN/v1/bucket" \
  -H "Content-Type: application/json" \
  -d '{"globalAliases": ["docker-images"]}')
BUCKET_ID=$(echo "$BUCKET_JSON" | jq -r '.id')

curl -sf -X POST "$GARAGE_ADMIN/v1/bucket/allow" \
  -H "Content-Type: application/json" \
  -d "{\"bucketId\": \"$BUCKET_ID\", \"accessKeyId\": \"$ACCESS_KEY\", \"permissions\": {\"read\": true, \"write\": true, \"owner\": true}}"

# Write creds for Jenkins
mkdir -p /shared
cat > /shared/garage-creds.env <<EOF
AWS_ACCESS_KEY_ID=$ACCESS_KEY
AWS_SECRET_ACCESS_KEY=$SECRET_KEY
AWS_ENDPOINT_URL=http://garage:3900
AWS_DEFAULT_REGION=garage
EOF

echo "Garage initialized. Bucket: docker-images"
```

Note: Garage admin API may need an admin token depending on version. Check if `admin.admin_token` needed in toml. If so, add it and pass to curl via `-H "Authorization: Bearer $TOKEN"`.
