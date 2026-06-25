# CySpace.com Part II

**Author:** raed

**Category:** Crypto

## Description

CySpace.com is back. Rebuilt from the original 1999 PHP source on a salvaged Pentium II, the pre-EMP social network is running again over dial-up. You've been tracking a Remnant operative known as `@viper92` since a suspicious AOL session was intercepted on their dial-up line. Their CySpace profile is public; their inbox is not. They sign every post with DSA - FIPS 186-1 (1994), the only signing standard in the salvaged codebase. Intel suggests their PHP signing module has a broken nonce generator. Recover the private key, forge a signed inbox-access request, and read what they're hiding.

### Files

[cyspace_posts.json](./release_files/cyspace_posts.json) - 50 signed posts from @viper92's timeline

[cyspace_params.py](./release_files/cyspace_params.py) - DSA domain parameters and @viper92's public key

[cyspace_api.txt](./release_files/cyspace_api.txt) - API protocol and canonical signing-envelope spec

[cyspace_signer.php.txt](./release_files/cyspace_signer.php.txt) - leaked legacy PHP signing module (the bug is in here)

### Host

`nc <host> <port>`

## Part 1

**CTFd name:** CySpace.com Part II

### CTFd Description

> CySpace.com is back, rebuilt from the original 1999 PHP source on a salvaged Pentium II, running over dial-up. You've been tracking Remnant operative @viper92 since a suspicious AOL session was intercepted on their line. Their CySpace profile is public; their inbox is not. They sign every post with DSA (FIPS 186-1, 1994), the only signing standard in the salvaged codebase, but intel suggests their PHP signing module has a broken post-EMP nonce generator. Somewhere in their 50-post timeline, two posts share the same nonce. Recover the private key, forge a signed inbox-access request per the API spec, and read what they're hiding.
.
>
> `nc <host> <port>`
>
> Files: [cyspace_posts.json](attachment), [cyspace_params.py](attachment), [cyspace_api.txt](attachment), [cyspace_signer.php.txt](attachment)

### Depends on

None (standalone - does not require solving CySpace.com Part I from 2025 Regionals)

### Flag

<details>
<summary>(expand to read)</summary><br>

`cybersci{s4me_k_tw1ce_1s_n0_s3cr3t_959463}`

</details>

### Walkthrough

<details>
<summary>(expand to read)</summary><br>

**Background — what DSA is and why k reuse breaks it**

A digital signature proves a message came from someone who holds a secret private key `x`, without revealing `x`. DSA exploits the **discrete logarithm problem**: given `g`, `p`, and `y = g^x mod p`, recovering `x` is computationally infeasible — so `y` (the public key) can be shared openly while `x` stays secret.

To sign a message, DSA picks a random per-signature secret called a **nonce** `k` and produces:

DSA signatures have the form `(r, s)` where:
```
r = (g^k mod p) mod q
s = k⁻¹ · (H(m) + x·r) mod q
```

Because `r` depends only on `k` (not on the message), if the same `k` is reused across two signatures, **r will be identical** for both. That's the fingerprint that exposes the reuse.

With two signatures `(r, s1)` and `(r, s2)` over messages with hashes `h1` and `h2`, you can subtract the two `s` equations to cancel `x·r` and solve directly for `k`:
```
k = (h1 - h2) · (s1 - s2)⁻¹  mod q
```
Once `k` is known, `x` falls out of either `s` equation immediately:
```
x = (s·k - H(m)) · r⁻¹  mod q
```
With `x` in hand you can forge a valid signature on any message — which is exactly what this challenge asks you to do. The leaked `cyspace_signer.php.txt` shows why: the post-EMP `cyspace_generate_nonce()` seeds `mt_rand` from `time()/60` (minute resolution) and caches a "broken_rng_state" flag, which can produce duplicate k values across posts signed in the same minute window.

**Step 1** - Read `cyspace_api.txt` to learn the canonical signing envelope:
```
<post_id>|<unix_timestamp>|@<author>|<body>
```
This is the byte string that gets fed to SHA-1 - NOT the raw `body`.

**Step 2** - Scan `cyspace_posts.json` (50 posts) for the duplicate-`r` pair:
```python
import json
posts = json.load(open("cyspace_posts.json"))
seen = {}
for p in posts:
    if p["r"] in seen:
        a, b = seen[p["r"]], p
        break
    seen[p["r"]] = p
```

**Step 3** - Reconstruct each envelope and compute SHA-1 digests:
```python
import hashlib
def envelope(p):
    return f'{p["post_id"]}|{p["timestamp"]}|@{p["author"]}|{p["body"]}'.encode()
def H(p):
    return int(hashlib.sha1(envelope(p)).hexdigest(), 16)
h1, h2 = H(a), H(b)
```

**Step 4** - Recover k and the private key x:
```python
from sympy import mod_inverse
r, s1, s2 = a["r"], a["s"], b["s"]
k = (h1 - h2) * mod_inverse(s1 - s2, q) % q
x = (s1 * k - h1) * mod_inverse(r, q) % q
assert pow(g, x, p) == y    # checkpoint: if this fails, fix the envelope reconstruction
```

**Step 5** - Forge a fresh signature for an inbox-request envelope (format in `cyspace_api.txt`):
```python
import secrets
req_id    = "INBOX-" + secrets.token_hex(4)
ts        = int(time.time())
req_env   = f"{req_id}|{ts}|@viper92|INBOX_REQUEST".encode()
req_h     = int(hashlib.sha1(req_env).hexdigest(), 16)
k_new     = secrets.randbelow(q - 1) + 1
r_new     = pow(g, k_new, p) % q
s_new     = mod_inverse(k_new, q) * (req_h + x * r_new) % q
```

**Step 6** - Connect to the server, send the envelope and `(r_new, s_new)` per the protocol, receive the flag.

The full solve script is in `solve_files/solve.py`.

</details>

## Setup instructions

### One-time VM prerequisite: install Docker

```bash
ssh vpcadmin@10.0.2.82
sudo apt-get update
sudo apt-get install -y ca-certificates curl
sudo install -m 0755 -d /etc/apt/keyrings
sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
sudo chmod a+r /etc/apt/keyrings/docker.asc
echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | sudo tee /etc/apt/sources.list.d/docker.list
sudo apt-get update
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin make
sudo usermod -aG docker vpcadmin
newgrp docker
```

Verify with `docker run hello-world` before proceeding.

### Deploy

1. Generate posts: `cd server_files && make posts` - creates a Python venv, installs dependencies, runs `generate_posts.py`, and writes `cyspace_posts.json` and `cyspace_params.py` to `release_files/` and `secret.txt` to `server_files/`.
2. Confirm `release_files/cyspace_signer.php.txt` contains `gmp_init("<REDACTED>", 16)` for the private key - the real `x` must never appear in release files.
3. Copy server files to the VM (run from challenge root):
   ```
   scp server_files/server.py server_files/secret.txt server_files/Dockerfile server_files/docker-compose.yml server_files/Makefile vpcadmin@10.0.2.82:~/cyspace2/
   ```
4. SSH to the VM and start the server:
   ```
   ssh vpcadmin@10.0.2.82
   cd ~/cyspace2 && make run
   ```
5. To stop the server: `make stop` (from `~/cyspace2` on the VM).
6. Verify end-to-end: `cd solve_files && python3 solve.py 10.0.2.82 1337` - should locate the duplicate-`r` pair, recover x via `pow(g,x,p)==y`, forge a valid inbox envelope, and print the flag.

### After a VM Restart

The Docker container does not start automatically on reboot. SSH to the VM and restart it:

```
ssh vpcadmin@10.0.2.81
cd ~/cyberkinz && make run
```

To make the container start automatically on boot, enable the Docker restart policy (already set to `unless-stopped` in `docker-compose.yml`) by ensuring Docker itself starts on boot:

```
sudo systemctl enable docker
```

This only needs to be run once. After that, future VM reboots will bring the container up automatically without manual intervention.
