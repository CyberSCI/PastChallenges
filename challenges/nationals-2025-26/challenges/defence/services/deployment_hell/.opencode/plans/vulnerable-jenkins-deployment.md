# Plan: Vulnerable Jenkins CTF Challenge — Deployment Hell

## Goal

Build a fully Dockerized, JCasC-driven Jenkins instance that is intentionally misconfigured
across a broad attack surface. Players must harden the Jenkins instance while keeping it and
its deployed canary application alive (patch-and-keep-alive mechanic).

Flag mechanics, scoring checker, and attack bot are **out of scope** for this plan.

---

## Architecture

```
docker-compose.yml
└── jenkins    ← Jenkins LTS, Docker socket mounted (extra vuln surface)
                  └── pipeline builds + deploys canary via host Docker daemon
```

The **canary app source** is baked into the Jenkins image (`COPY` in Dockerfile) at
`/var/jenkins_home/canary`. Jenkins' `deploy-canary` pipeline builds it into a Docker image
and runs it as a standalone container on the host Docker daemon.

The Docker Compose stack has **one service only**: `jenkins`.

---

## Vulnerability Surface

All misconfigurations live in `jenkins/casc/jenkins.yaml`, annotated with `# VULN:` comments
so players can locate and understand each issue.

| Vulnerability | Mechanism |
|---|---|
| No authentication | JCasC: `securityRealm: legacy`, `authorizationStrategy: unsecured` |
| Script console enabled | Default Jenkins behaviour — no restriction |
| CSRF protection disabled | JCasC: `crumbIssuer: "none"` |
| Agent-to-master security disabled | JCasC: `remotingSecurity.enabled: false` |
| Jenkins CLI exposed over HTTP | JCasC: `cli: true` |
| Docker socket mounted | `docker-compose.yml`: `/var/run/docker.sock:/var/run/docker.sock` — host escape |

---

## File Layout

```
deployment_hell/
├── README.md
├── release_files/                    ← Identical to server_files (players get full source)
│   ├── docker-compose.yml
│   ├── jenkins/
│   │   ├── Dockerfile
│   │   ├── plugins.txt
│   │   └── casc/
│   │       └── jenkins.yaml
│   └── canary/
│       ├── Dockerfile
│       └── app.py
├── server_files/
│   ├── docker-compose.yml            ← Same as release (secrets injected later)
│   ├── jenkins/
│   │   ├── Dockerfile
│   │   ├── plugins.txt
│   │   └── casc/
│   │       └── jenkins.yaml
│   └── canary/
│       ├── Dockerfile
│       └── app.py
└── solve_files/
    └── solve.md
```

> `release_files/` and `server_files/` are identical for now. When flag mechanics are added
> later, secrets will only exist in `server_files/`.

---

## Detailed File Contents

### `docker-compose.yml` (same in both `release_files/` and `server_files/`)

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
      # VULN: Docker socket gives Jenkins (and any attacker) root-equivalent access to the host
      - /var/run/docker.sock:/var/run/docker.sock
    environment:
      - JAVA_OPTS=-Djenkins.install.runSetupWizard=false
      - CASC_JENKINS_CONFIG=/var/jenkins_home/casc_configs
    restart: unless-stopped

volumes:
  jenkins_home:
```

---

### `jenkins/Dockerfile`

```dockerfile
FROM jenkins/jenkins:lts

USER root
# Install Docker CLI so Jenkins pipelines can run docker commands
RUN apt-get update \
    && apt-get install -y docker.io \
    && rm -rf /var/lib/apt/lists/* \
    && usermod -aG docker jenkins

USER jenkins

ENV JAVA_OPTS="-Djenkins.install.runSetupWizard=false"
ENV CASC_JENKINS_CONFIG=/var/jenkins_home/casc_configs

COPY jenkins/plugins.txt /usr/share/jenkins/ref/plugins.txt
RUN jenkins-plugin-cli --plugin-file /usr/share/jenkins/ref/plugins.txt

COPY jenkins/casc/ /var/jenkins_home/casc_configs/

# Bake canary source into the image so the deploy pipeline can build it
COPY --chown=jenkins:jenkins canary/ /var/jenkins_home/canary/
```

> All paths are relative to the build context (the `release_files/` or `server_files/` dir),
> because `docker-compose.yml` sets `context: .`.

---

### `jenkins/plugins.txt`

```
configuration-as-code
job-dsl
git
workflow-aggregator
docker-workflow
matrix-auth
```

**Plugin purposes:**
- `configuration-as-code` — enables JCasC YAML loading
- `job-dsl` — lets `jenkins.yaml` define jobs as code
- `git` — pipeline Git checkout support
- `workflow-aggregator` — Declarative Pipeline support
- `docker-workflow` — `docker` steps in pipelines
- `matrix-auth` — needed for players to configure proper authorization later

---

### `jenkins/casc/jenkins.yaml`

```yaml
jenkins:
  # VULN: No authentication — anyone can access Jenkins without credentials
  securityRealm:
    legacy: {}

  # VULN: No authorization — all actions permitted to all users including anonymous
  authorizationStrategy:
    unsecured: {}

  # VULN: CSRF protection disabled — allows cross-site request forgery attacks
  crumbIssuer: "none"

  # VULN: Agent-to-master security disabled — agents can read/write any file on master
  remotingSecurity:
    enabled: false

  # VULN: CLI accessible over HTTP without credentials
  cli: true

  numExecutors: 2

jobs:
  - script: |
      pipelineJob('deploy-canary') {
        definition {
          cps {
            script('''
              pipeline {
                agent any
                stages {
                  stage('Build') {
                    steps {
                      sh 'docker build -t canary /var/jenkins_home/canary'
                    }
                  }
                  stage('Deploy') {
                    steps {
                      sh """
                        docker rm -f canary || true
                        docker run -d --name canary -p 9000:9000 canary
                      """
                    }
                  }
                  stage('Verify') {
                    steps {
                      sh 'curl -sf http://localhost:9000/health || exit 1'
                    }
                  }
                }
              }
            ''')
          }
        }
        triggers {
          cron('H/5 * * * *')
        }
      }
```

---

### `canary/app.py`

```python
from http.server import BaseHTTPRequestHandler, HTTPServer

PORT = 9000


class CanaryHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/health":
            self._respond(200, "OK")
        else:
            self._respond(404, "Not Found")

    def _respond(self, code, body):
        self.send_response(code)
        self.send_header("Content-Type", "text/plain")
        self.end_headers()
        self.wfile.write(body.encode())

    def log_message(self, format, *args):
        pass  # suppress default request logging


if __name__ == "__main__":
    server = HTTPServer(("0.0.0.0", PORT), CanaryHandler)
    print(f"Canary listening on :{PORT}")
    server.serve_forever()
```

---

### `canary/Dockerfile`

```dockerfile
FROM python:3.12-slim
WORKDIR /app
COPY app.py .
EXPOSE 9000
CMD ["python", "app.py"]
```

---

### `solve_files/solve.md` (stub)

A hardening walkthrough stub — to be completed once flag mechanics are decided. Should cover:

1. Enable authentication (add an admin user in JCasC)
2. Enable authorization (restrict anonymous access via matrix-auth)
3. Re-enable CSRF protection (remove `crumbIssuer: "none"`)
4. Re-enable agent-to-master security
5. Disable CLI over HTTP
6. Remove or restrict the Docker socket mount
7. Confirm the canary deploy pipeline still runs successfully

---

## Implementation Notes

### Build context and COPY paths

`docker-compose.yml` sets `context: .`, which means the build context is the `release_files/`
(or `server_files/`) directory. All `COPY` directives in `jenkins/Dockerfile` must use paths
relative to that root — e.g. `COPY canary/ ...` not `COPY ../canary/ ...`.

### Plugin installation

`jenkins-plugin-cli` is included in `jenkins/jenkins:lts` images since Jenkins 2.346+.
No additional tooling is needed.

### JCasC loading

`CASC_JENKINS_CONFIG` points to a directory; all `*.yaml` files in it are loaded at startup.
A single `jenkins.yaml` is sufficient.

### Job DSL approval

By default Jenkins requires script approval for Job DSL scripts. To avoid a manual click
blocking first-boot, the JCasC `jenkins.yaml` should include:

```yaml
security:
  scriptApproval:
    approvedSignatures:
      - "method groovy.lang.GroovyObject invokeMethod java.lang.String java.lang.Object"
```

Or alternatively, set `authorizationStrategy: unsecured` already disables most safety checks,
so the approval dialog may not appear. Verify during implementation and adjust if needed.

---

## Out of Scope (Future Plans)

- Flag mechanics (how/where the flag is stored and awarded)
- Scoring checker (external or platform-provided)
- Attack bot (provided by CTF platform separately)
- Full README content (depends on flag decisions)
