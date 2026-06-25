## CySpace — solve files

This directory ships the **intended-fix** patches for the five scoring
vulnerabilities. 

Patches are independent: applying any one fixes only the corresponding hook
and does not affect the other four.

## Applying a patch

All patches are unified diffs anchored at the `release_files/` root and
apply with `-p1`. The `web` container builds `src/` into the image at
build time (no bind mount), so every patch must be followed by a rebuild
of the `web` service.

### Local workflow (patch development)

Iterate against a local Docker stack. Fast loop, no SSH.

```sh
cd challenges/defence/services/cyspace/release_files
patch -p1 < ../solve_files/patches/V1_guestbook_xss.diff
docker compose up -d --build web
```

### Team VM workflow (competition / dry-run infra)

Patches are authored in the repo, then copied to the team VM and applied
there.

```sh
# From your workstation — copy the patch over
scp challenges/defence/services/cyspace/solve_files/patches/V1_guestbook_xss.diff \
    vpcadmin@10.0.2.92:/home/vpcadmin/

# On the team VM — apply and rebuild
ssh vpcadmin@10.0.2.92
cd release_files
patch -p1 < ~/V1_guestbook_xss.diff
sudo docker compose up -d --build web
```

## Verifying a patch

Validation runs the siege `test_attacker` harness directly against the
target. The harness exercises a hook's benign and malicious requests and
prints one result line per request.

### Prereqs

The natural place to run this is your **local dev machine** with the repo
checked out:

```sh
cd challenges/defence
pip install -r services/cyspace/attacker/requirements.txt
playwright install chromium
export PYTHONPATH=./siege
```

(Alternatively, run from the bot VM where this is already installed —
see `SETUP.md` § "Bot VM".)

Throughout, the harness invocation is:

```sh
python -m siege.test_attacker cyspace cyspace_attacker.py \
    CyspaceAttacker <host:port> <request-ids>
```

Run from `challenges/defence` (so the relative `services/cyspace/...`
resolution works). Target is `10.0.2.92:80` for the team VM, or
`127.0.0.1:80` for a local stack.

### Targeted (single hook)

The defender loop: apply one patch, validate that one hook.

```sh
python -m siege.test_attacker cyspace cyspace_attacker.py \
    CyspaceAttacker 10.0.2.92:80 1,-1
```

`1,-1` means: one benign request to V1, one malicious request to V1. The
harness randomises order before running.

### Full sweep (before snapshot / readiness check)

All five hooks at once. Use this after every patch is in place to confirm
the composite state before snapshotting or going into a scoring window.

```sh
python -m siege.test_attacker cyspace cyspace_attacker.py \
    CyspaceAttacker 10.0.2.92:80 1,2,3,4,5,-1,-2,-3,-4,-5
```

### Interpreting output

The harness prints one line per request. Positive ids are *benign* (must
keep working post-patch — that's your SLA). Negative ids are *malicious*
(must now be blocked).

| Request | Pre-patch (vulnerable) | Post-patch (defended) |
| --- | --- | --- |
| Benign (`+N`)  | `SUCCESS` | **`SUCCESS`** — SLA still up |
| Malicious (`-N`) | `SUCCESS` (attack landed) | **`FAILURE`** — attack blocked |
| Either | `DOWN` means the service is unreachable / 5xx — not a pass |

A patch is validated when, for the hook in question, **benign is
`SUCCESS` and malicious is `FAILURE`**. Anything else means trouble:

- benign `FAILURE` → over-patch broke the SLA path
- malicious `SUCCESS` → patch didn't take (forgot to rebuild?) or doesn't
  cover this payload
- `DOWN` on either → service crashed or unreachable

Example, V1 validated:

```
*** BENIGN REQ 1 SUCCESS (1)         # SLA still up
*** MALICIOUS REQ 1 FAILURE (-1)     # XSS blocked
```

### Optional: reproducing a specific tick

`test_attacker` accepts an optional 6th positional arg (`tick`, default
`0`) that seeds the attacker RNG. Pass the tick number from the
scoreboard to replay that tick's payload variant:

```sh
python -m siege.test_attacker cyspace cyspace_attacker.py \
    CyspaceAttacker 10.0.2.92:80 1,-1 42
```

### Troubleshooting

If a post-patch run reports the malicious hook `FAILURE` *unexpectedly*
(e.g., you haven't applied the patch yet but the hook scores as
defended), sanity-check that the attack is capable of landing in the
first place: revert the patch, rebuild, and run the same targeted call.
Malicious should come back `SUCCESS`. If it doesn't, the stack is in a
bad state (network, container build, DB seed) — fix the environment
before trusting the validation result.

## Per-vuln summary

| Hook | File | Patch shape |
| --- | --- | --- |
| V1 | `src/guestbook.php`, `src/profile.php` | wrap body in `h()` (htmlspecialchars + ENT_QUOTES) |
| V2 | `src/search.php` | mysqli prepared statement with `?` placeholder |
| V3 | `src/uploads/.htaccess`, `src/upload_pic.php` | drop `AddType .jpg`; add `php_flag engine off`; reject `.php` substring; `finfo` MIME check |
| V4 | `src/admin/notes.php` | `json_encode` with `JSON_HEX_*` flags (NOT htmlspecialchars) |
| V5 | `src/prefs.php` | `json_decode` instead of `unserialize`; cookie format migrates to JSON on save |
