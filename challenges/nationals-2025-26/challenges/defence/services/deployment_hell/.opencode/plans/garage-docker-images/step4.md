# Step 4: Compose & Init

## `compose.yaml`

Add shared volume for creds, init service, update Jenkins build context:

```yaml
services:
  jenkins:
    build:
      context: .
      dockerfile: jenkins/Dockerfile
    ports:
      - "8080:8080"
      - "50000:50000"
    volumes:
      - jenkins_home:/var/jenkins_home
      - /var/run/docker.sock:/var/run/docker.sock
      - shared:/shared
    environment:
      - JAVA_OPTS=-Djenkins.install.runSetupWizard=false
      - CASC_JENKINS_CONFIG=/var/jenkins_home/casc_configs
    restart: unless-stopped
    depends_on:
      garage-init:
        condition: service_completed_successfully

  garage:
    image: dxflrs/garage:latest
    container_name: garage
    restart: unless-stopped
    volumes:
      - ./garage/garage.toml:/etc/garage.toml
      - garage_data:/var/lib/garage/data
      - garage_meta:/var/lib/garage/meta
    ports:
      - "3900:3900"
      - "3901:3901"
      - "3902:3902"

  garage-init:
    image: curlimages/curl:latest
    volumes:
      - shared:/shared
      - ./garage/init.sh:/init.sh:ro
    entrypoint: ["/bin/sh", "/init.sh"]
    depends_on:
      - garage

volumes:
  garage_data:
  garage_meta:
  jenkins_home:
  shared:
```

Changes:
- Added `shared` volume (Jenkins + garage-init both mount it)
- Added `garage-init` one-shot service that runs init.sh
- Jenkins depends on garage-init completing
- `garage-init` uses `curlimages/curl` (has curl + sh, lightweight). May need `jq` — if not available, switch to a different base image or parse JSON with sed/grep.

## Note on garage-init image

`curlimages/curl` may not have `jq`. Alternatives:
- Use `alpine` and `apk add curl jq` in entrypoint
- Or inline the init.sh to use grep/sed for JSON parsing

Safer to use `alpine` with install step. Update `garage-init`:

```yaml
  garage-init:
    image: alpine:latest
    volumes:
      - shared:/shared
      - ./garage/init.sh:/init.sh:ro
    entrypoint: ["/bin/sh", "-c", "apk add --no-cache curl jq && /bin/sh /init.sh"]
    depends_on:
      - garage
```
