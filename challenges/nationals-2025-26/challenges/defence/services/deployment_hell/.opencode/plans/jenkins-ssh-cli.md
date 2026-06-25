# Plan: Jenkins SSH CLI Access

## Overview
Enable SSH CLI access to Jenkins for all 3 users (admin, sofia.bernhard, michael.fateh) using SSH keys. Web UI remains as fallback. Keys embedded directly in CasC.

## Changes

### 1. `server_files/jenkins/casc/jenkins.yaml`

**Add SSHD port config** under `security:`:
```yaml
security:
  globalJobDslSecurityConfiguration:
    useScriptSecurity: false
  sshd:
    port: 2222
```

**Add SSH public keys to each user** via `sshPublicKey` property. Example for admin:
```yaml
- id: "admin"
  name: "Administrator"
  password: "3af23c474f6c4c6ebaca02e743433043"
  properties:
    - "apiToken"
    - "consoleUrlProvider"
    - "viewsTabBar"
    - myView:
        viewsTabBar: "standard"
    - "timezone"
    - "experimentalFlags"
    - sshPublicKey:
        authorizedKeys: "ssh-ed25519 AAAA... admin"
```

Repeat for `sofia.bernhard` and `michael.fateh` with their respective public keys.

**Note:** Exact CasC property name for SSH authorized keys needs verification against the installed `sshd` plugin version. The property is either `sshPublicKey` or `authorizedKeysCommand` — check plugin docs or export existing config via `JENKINS_URL/configuration-as-code/export`.

### 2. `server_files/compose.yaml`

Add port `2222` to jenkins service:
```yaml
jenkins:
  ports:
    - "8080:8080"
    - "50000:50000"
    - "2222:2222"
```

### 3. Pre-generate SSH keys

Generate 3 ed25519 key pairs (one per user). Store in `keys/` directory. Embed `.pub` contents in CasC yaml (step 1).

```bash
cd server_files/keys
ssh-keygen -t ed25519 -f ./admin -N ""
ssh-keygen -t ed25519 -f ./sofia.bernhard -N ""
ssh-keygen -t ed25519 -f ./michael.fateh -N ""
```

## What NOT to change
- `jenkins/Dockerfile` — sshd plugin already installed
- `keys/generate.fish` — leave as-is per user request
- Existing password auth — SSH is additive, not replacement

## Verification

```bash
# Test SSH CLI connection
ssh -p 2222 -i keys/admin admin@localhost help

# Run a build
ssh -p 2222 -i keys/admin admin@localhost build build-and-upload

# List jobs
ssh -p 2222 -i keys/admin admin@localhost list-jobs
```

## Risk note
SSH CLI with `loggedInUsersCanDoAnything` means any user with SSH access gets full Jenkins control — same as web UI. Consistent with existing vuln surface.
