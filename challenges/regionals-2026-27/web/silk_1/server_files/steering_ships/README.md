# Steering Ships

## Development

When running locally, add these entries to your hosts file:

```
127.0.0.1 ships.damoverflow.com
127.0.0.1 api.ships.damoverflow.com
127.0.0.1 auth.ships.damoverflow.com
```

Copy the `.env.example` file to `.env` and add an admin password:

```
KC_BOOTSTRAP_ADMIN_PASSWORD=example
```

Generate a self-signed certificate:

```sh
openssl req -x509 -nodes -days 825 -newkey rsa:2048 -keyout ./reverse-proxy/dev.key -out ./reverse-proxy/dev.crt -subj "/CN=ships.damoverflow.com" -addext "subjectAltName=DNS:auth.ships.damoverflow.com,DNS:ships.damoverflow.com,DNS:api.ships.damoverflow.com" -addext "basicConstraints=critical,CA:FALSE" -addext "keyUsage=critical,digitalSignature,keyEncipherment" -addext "extendedKeyUsage=serverAuth"
```

Build/start the applications:

```
docker compose up -d --build
```

Access the application: https://ships.damoverflow.com

## Map Data

The radar coastline, islands, and river-water polygons use the included OpenStreetMap extract at `controller_plus_frontend/src/saint-john-map.json`; attribution is shown on the chart. The data is available under the ODbL.

## Keycloak Hint

To the CyberSci competitors: I recommend you do not waste time attempting to re-use the secrets within realm.json against production. Production uses different HMAC/RSA/AES secrets than are provided in your realm.json file.
