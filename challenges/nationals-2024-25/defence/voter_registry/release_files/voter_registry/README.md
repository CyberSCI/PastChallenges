# Voter Registry

This application allows voters to register to vote online and lookup their assigned polling station.

## For Competitors

These are the default admin credentials for Keycloak:
```
admin
Cybersci@foHIF0l
```

These are some application admin credentials (do not change the existing admins' passwords):
```
dcastell
Ic3Falcon!92

imontez
booted-unearned-entomb-backtalk-portable-jittery
```

You can rebuild the service with:

```
sudo docker compose build
```

You can deploy the new build with:
```
sudo docker compose up -d
```

### To Fully Reset

If you need to fully reset, run these commands:

```
# Spin down the service
cd /home/vpcadmin/voter_registry
docker compose down

# Delete the service files
cd /home/vpcadmin
sudo rm -rf voter_registry

# Rebuild the service
unzip voter_registry.zip
cd voter_registry
docker compose up -d --build
```