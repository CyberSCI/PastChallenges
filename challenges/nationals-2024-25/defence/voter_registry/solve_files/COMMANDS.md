# Voter Registry Useful Commands

Export realm to JSON:

```sh
docker compose exec keycloak /opt/keycloak/bin/kc.sh export --dir /tmp --realm voter-registry --users realm_file
docker compose cp keycloak:/tmp/voter-registry-realm.json .
```

Create certificates:

```sh
openssl req -x509 -newkey rsa:4096 -sha256 -days 365 -nodes -keyout ./traefik/certs/register.valverde.vote.key -out ./traefik/certs/register.valverde.vote.crt -subj "/CN=register.valverde.vote" -addext "subjectAltName=DNS:register.valverde.vote,DNS:api.register.valverde.vote,DNS:auth.register.valverde.vote"
```

Testing attack script locally (from within `challenges/defence/voter_registry/server_files/attack_bot/voter_registry_attacker`):

```sh
PYTHONPATH="../../../../siege/:." python3 ../../../../siege/siege/test_attacker.py voter_registry_attacker.py VoterRegistryAttacker 127.0.0.1:443 1,2,3,4,5,-1,-2,-3,-4,-5 TICKNUMBER
```