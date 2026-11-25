# DamWatch: The Diversion Protocol

**Author:** Jon / chronoblaze

**Category:** Web

## Description

The lake level is falling, but DamWatch says everything is normal. An AI maintenance system has opened a diversion to cool its data center. You have observer access to the colony's console. Find the work order and lock the gates before the lake is drained.

One hosted web app, three separately scored flags, one Docker container on the assigned VM.

### Files

None for players. The web app contains the necessary client-side clues.

### Host

`https://damwatch.damoverflow.com` — use this same URL for all three CTFd entries. (Dev VM: `10.0.2.31`, reachable over the regionals VPN.)

## Part 1

**CTFd name:** DamWatch 1: Crossed Signals

### CTFd Description

The dashboard says NORMAL. The waterline disagrees. Its live connection carries more than water levels. Find the incident behind the maintenance entry.

### Depends on

None.

### Flag

<details>
<summary>(expand to read)</summary><br>

cybersci{n01s3_0n_th3_w1r3}

</details>

### Walkthrough

<details>
<summary>(expand to read)</summary><br>

1. Open the dashboard. This creates an observer session. In the browser's network view or Burp, watch the connection to `/ws/telemetry`. The page sends `{"action":"subscribe","topic":"water/level"}` and receives the public gauge reading. The 03:14 feed entry calls the drawdown a north-spillway test while the status still says NORMAL.
2. Open `/api/topics`. It lists `operations/triage` as restricted but gives no incident data. Keep the same session cookie and send `{"action":"subscribe","topic":"operations/triage"}` over the WebSocket. Burp's WebSocket Repeater or a small WebSocket client can send the frame.
3. The server checks the observer session but omits the permission check for this topic. Its `INC-017` response contains the first flag in the `flag` field and names `coolant-diversion.memo` for Part 2. A public subscription or passive page load does not return the incident.

</details>

### Optional hint

<details>
<summary>(expand to read)</summary><br>

Watch the live connection, including topics the page does not subscribe to.

</details>

## Part 2

**CTFd name:** DamWatch 2: Hidden Current

### CTFd Description

The incident names a memo that does not appear in the public archive. Find it.

### Depends on

DamWatch 1: Crossed Signals.

### Flag

<details>
<summary>(expand to read)</summary><br>

cybersci{r00ts_run_d33p}

</details>

### Walkthrough

<details>
<summary>(expand to read)</summary><br>

1. Open `/reports` and select a public record. The browser requests `/api/archive/read?path=public%2Fstatus.txt` (or another `public/` record). The public list does not contain the memo from `INC-017`.
2. Change the `path` value to `public/../internal/coolant-diversion.memo`. In a URL, that can be sent as `path=public%2F..%2Finternal%2Fcoolant-diversion.memo`. A direct `internal/coolant-diversion.memo` path returns 404.
3. The reader checks the raw `public/` prefix before normalizing `..`, so the lookup lands on the internal memo. Its `body` contains the second flag after `Inspector's evidence mark:`. The memo also explains why the manual lock needs receipts for slots A and B despite issuing one receipt per emergency ticket. These are fixed logical records; the request cannot read files from the VM.

</details>

### Optional hint

<details>
<summary>(expand to read)</summary><br>

The archive checks a name before it resolves its path.

</details>

## Part 3

**CTFd name:** DamWatch 3: Double Approval

### CTFd Description

The manual lock needs two approval receipts. Your session has one ticket. Stop the diversion.

### Depends on

DamWatch 2: Hidden Current.

### Flag

<details>
<summary>(expand to read)</summary><br>

cybersci{r4c3_4g41nst_th3_cl0ck}

</details>

### Walkthrough

<details>
<summary>(expand to read)</summary><br>

1. Open `/override` with the same observer session. `GET /api/override/state` supplies the current `ticket`, generation, receipt slots, and lock status. Redeeming A and then B in the normal UI shows the problem: the first `POST /api/approvals/redeem` spends the ticket, and the second returns HTTP 409 `ticket_used`.
2. Issue a fresh ticket with `POST /api/approvals/reset` if the current one was spent. Send two `POST /api/approvals/redeem` requests at the same time, using the **same cookie and ticket**. Their JSON bodies differ only in `"slot":"A"` versus `"slot":"B"`. Burp's parallel-send feature or two client threads can create the overlap.
3. Both requests can pass the unused-ticket check before the audit wait finishes. Each returns an opaque `receipt`. If one returns 409, reset and try again after the two-second reset cooldown. Receipts from a previous generation cannot be reused.
4. Send `POST /api/override/authorize` with `{"receipts":{"A":"<A receipt>","B":"<B receipt>"}}`. Two distinct receipts from the same session and generation engage the lock. The success response says `Manual lock engaged. Cooling Annex intake closed.` and returns the third flag in its `flag` field. The public gauge and other teams' sessions stay unchanged.

</details>

### Optional hint

<details>
<summary>(expand to read)</summary><br>

One ticket, two slots: consider when the ticket becomes used.

</details>

## Setup instructions

Run these commands from this challenge folder on the assigned Linux VM (`10.0.2.31`). Docker Compose must be installed. Copy `server_files/env.example` to `$HOME/.config/damwatch/damwatch.env`, outside this folder and owned by the account running Compose. Fill `DAMWATCH_FLAG_1`, `DAMWATCH_FLAG_2`, and `DAMWATCH_FLAG_3` from the matching Flag dropdowns above, and set `DAMWATCH_PUBLIC_ORIGIN=https://damwatch.damoverflow.com` (exact browser origin, no trailing slash). The dropdowns and that env file are the only places the flag values should ever appear; keep them out of `env.example`, scripts, and anything player-facing.

Create the private directory and file, then restrict access:

```sh
mkdir -p "$HOME/.config/damwatch"
chmod 700 "$HOME/.config/damwatch"
cp server_files/env.example "$HOME/.config/damwatch/damwatch.env"
chmod 600 "$HOME/.config/damwatch/damwatch.env"
nano "$HOME/.config/damwatch/damwatch.env"
```

The default host port is 18027 and is published on `127.0.0.1` only. The app flags above go in the env file only; CTFd entries get the separate flag values the organizers provide (two-tier flag system).

```sh
export DAMWATCH_ENV_FILE="$HOME/.config/damwatch/damwatch.env"
docker compose -f server_files/docker-compose.yml config --quiet
docker compose -f server_files/docker-compose.yml up -d --build
docker compose -f server_files/docker-compose.yml ps
curl --fail http://127.0.0.1:18027/healthz
```

To rebuild after a source change, rerun `docker compose -f server_files/docker-compose.yml up -d --build`. To stop and remove the service, run `docker compose -f server_files/docker-compose.yml down`. To inspect recent startup errors, run `docker compose -f server_files/docker-compose.yml logs --tail=50`. A missing flag makes the app fail startup rather than serve a placeholder. The image has one non-root Uvicorn worker; sessions and receipts are held in that worker's memory, so a restart resets app progress while CTFd solves remain recorded.

nginx on the VM terminates TLS for `https://damwatch.damoverflow.com` and proxies to `127.0.0.1:18027`. From another machine, open the URL, check that the live reading arrives over WSS, and run `python solve_files/solve.py https://damwatch.damoverflow.com` after installing `solve_files/requirements.txt`. The reference solver prints all three flags.

### Reverse proxy notes

The app caps global state (2000 sessions, 500 WebSockets) as a backstop, but it can't tell one team's traffic from another without trusting forwarding headers, so per-source rate limiting goes on the proxy:

```nginx
limit_req_zone $binary_remote_addr zone=damwatch_http:10m rate=1r/s;
limit_req_zone $binary_remote_addr zone=damwatch_ws:10m rate=1r/s;
```

What the proxy has to get right:

- Forward WebSocket upgrades on `/ws/telemetry` (HTTP/1.1 plus `Upgrade`/`Connection` headers) and don't strip `Origin`.
- `proxy_read_timeout` above 300s, the app's WS idle timeout.
- `DAMWATCH_PUBLIC_ORIGIN` must match the browser origin exactly. The WS endpoint closes with code 1008 on an `Origin` mismatch, which would break Part 1 while everything else looks fine. Clients that send no `Origin` (scripts, Burp) are allowed.
- `limit_req zone=damwatch_http burst=10 nodelay; limit_req_status 429;` on `/`, burst=3 on `/ws/telemetry`. Teams behind one NAT share an IP, so keep the burst generous.
- The `Secure` cookie is set automatically since the public origin is HTTPS.

Sanity checks on the VM: WSS live reading in a browser, `solve.py` from a fresh session, and a `GET /` flood from one host returning 429s while another host still solves. Container logs are capped in the Compose file (`max-size: 10m`, `max-file: 3`).

**CTFd:** three Web entries with the Part names and descriptions above, same URL in each Connection Info. Dynamic scoring: 500 points initial, logarithmic, 40 solves to the 100-point minimum. Part 1 is visible immediately; in Requirements, Part 2 requires Part 1 and Part 3 requires Part 2, locked entries set to Anonymized. Two-tier flags: enter the organizer-provided CTFd flag values here, not the app flags in the dropdowns above. The app doesn't enforce solve order; CTFd does.

No player download or `release_files/` folder is required. This folder lives at `challenges/web/damwatch` in the competition repo.
