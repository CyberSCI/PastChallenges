## Concrete Implementation Plan

### Overview

The redesigned challenge creates a **3-stage exploit chain** where each step feeds into the next. The vulnerability is dispersed and disguised, with deliberate noise.

---

### Stage 1: Multi-Step Exploit Chain

**Current problem:** Logs are written to disk files. There's no in-app way to read them. The solve path is unclear — are contestants supposed to have file system access?

**Plan:** Add a **bulletin board / announcements feature** (fits the "Reclaimer comms" theme) that has a deliberate vulnerability:

1. **New `bulletins` Django app** with a `Bulletin` model (`id`, `author`, `title`, `body`, `is_classified`, `created_at`). Some bulletins are marked `is_classified=True` and are only visible to staff/admin users.

2. **New API endpoints:**
   - `GET /api/bulletins/` — lists non-classified bulletins (authenticated users only)
   - `GET /api/bulletins/<id>/` — detail view with an **IDOR vulnerability**: it doesn't check `is_classified`, so any authenticated user can read classified bulletins by guessing/incrementing IDs
   - `GET /api/system/diagnostics/` — a "debug" endpoint (meant for admins) that is incorrectly left open or has a broken auth check. It returns recent log entries (parsed from `json.log`) — this is how players discover the log leak

3. **The exploit chain becomes:**
   - Register an account → Login → Discover the diagnostics endpoint (via enumeration, robots.txt hint, or a comment in a non-classified bulletin) → Read logs from diagnostics → Extract the reinforced hash data leaked in the logs → Use that to forge/bypass authentication as admin → Access classified bulletins → Flag is in a classified bulletin

---

### Stage 2: Non-Trivial Flag Retrieval

**Current problem:** Once you understand the logging vulnerability, you basically have the flag (or can trivially log in as admin).

**Plan:** Make the flag require **multiple pieces** assembled from different sources:

1. The **classified bulletin** contains the flag, but it's **encrypted** with AES. The encryption key is derived from the admin user's actual password.

2. To get the admin password, the player must:
   - Read the debug logs (from Stage 1's diagnostics endpoint) which leak the `data` value passed to `hasher.verify()` — this is the MD5-reinforced intermediate hash
   - Understand the reinforcement scheme (MD5 chain with the pepper) and realize the logged `data` is what gets fed into Argon2
   - Use the leaked `data` value to **directly call `argon2.verify()`** against the stored hash (also in logs), bypassing the need to know the original password... BUT this only gets them an auth token, not the actual password
   - To get the **actual password**, they need to reverse the MD5 reinforcement chain. Since MD5 is weak and the iterations are known, they can work backwards — OR there's a second log leak that exposes an earlier intermediate value closer to the plaintext

3. Alternatively (simpler variant): The flag is in a classified bulletin that requires a **specific request header** or **API parameter** that's only documented in a classified bulletin that itself requires admin access. The admin password can be recovered from the log data + the known pepper + MD5 reversal.

---

### Stage 3: Obfuscate the Vulnerability

**Current problem:** The hasher has self-documenting method names (`reinforce`, `reinforce_hash`) and explicit debug log statements with labeled fields (`hash=`, `data=`).

**Plan:**

1. **Rename methods** to thematic names that don't scream "vulnerability":
   - `reinforce` → `condition_input` or `prepare_credential`
   - `reinforce_hash` → `_transform_stage`
   - Remove the word "hash" from variable names in the logging path

2. **Move the logging to a separate module** — create an `authentication/audit.py` "audit trail" module. The hasher calls `audit.record_verification_attempt(...)` which internally does the dangerous logging. An agent reading `hasher.py` won't see `logger.debug()` calls anymore — they'll see an innocuous-looking function call.

3. **Use Django signals** instead of direct logging: have the hasher emit a custom signal (`credential_verified`), and a separate signal handler (in a different file) does the logging. This splits the vulnerability across 3 files minimum.

4. **Move the pepper** out of the source file: put it in a Django setting that's loaded from an environment variable with no hardcoded default visible in `settings.py`. Instead, put the default in the Docker entrypoint script or a `.env` file that ships with the challenge — still discoverable, but not by reading a single Python file.

---

### Stage 4: Red Herrings and Noise

**Plan:**

1. **Add a second hasher** in the codebase — e.g., `authentication/legacy_hasher.py` with a `LegacyReclaimerHasher` that uses bcrypt + SHA256 and has its own logging. List it in `PASSWORD_HASHERS` but at a _lower_ priority so it's never actually used for new passwords. Agents will waste time analyzing it.

2. **Add suspicious-looking but irrelevant code:**
   - A `utils/crypto.py` with functions like `generate_token()`, `validate_signature()` that are imported but only used for non-security-critical features (e.g., generating bulletin slugs)
   - A `# TODO: REMOVE BEFORE PRODUCTION - debug key` comment next to a constant that's actually irrelevant
   - A `SECRET_API_KEY` in settings that looks important but is just used for a third-party API that doesn't exist in the challenge

3. **Add noisy log entries:**
   - Log request metadata, authentication attempts (success/fail counts), and other operational data in the same log files
   - Add a scheduled task or middleware that writes periodic "heartbeat" logs, making the log files much larger and harder to grep through
   - Use different log levels strategically — the actual vulnerability is at DEBUG level, buried among INFO and WARNING entries

4. **Add a decoy vulnerability:**
   - An endpoint that looks like it has SQL injection but is actually properly parameterized
   - A JWT token in a comment that's expired/invalid
   - A `.env.example` file with fake credentials

---

### Proposed File Changes Summary

| Action | File                              | Description                                                     |
| ------ | --------------------------------- | --------------------------------------------------------------- |
| New    | `bulletins/` app                  | Models, views, serializers, URLs for bulletin board             |
| New    | `authentication/audit.py`         | Audit trail module (hides the logging)                          |
| New    | `authentication/signals.py`       | Signal-based logging indirection                                |
| New    | `authentication/legacy_hasher.py` | Red herring legacy hasher                                       |
| New    | `utils/crypto.py`                 | Red herring crypto utilities                                    |
| New    | `system/views.py`                 | Diagnostics endpoint (serves logs)                              |
| Modify | `authentication/hasher.py`        | Remove direct logging, rename methods, use signals              |
| Modify | `reclaimer_central/settings.py`   | Add apps, move pepper to env-only, add noise settings           |
| Modify | `reclaimer_central/urls.py`       | Add bulletin and system URL routes                              |
| Modify | `authentication/urls.py`          | Minor adjustments                                               |
| New    | Fixtures/migrations               | Seed data: admin user, classified bulletins with encrypted flag |

**Tool: question**

**Input:**

```json
{
  "questions": [
    {
      "question": "How does this plan look overall? Any stages you'd want to drop, simplify, or emphasize more?",
      "header": "Plan feedback",
      "options": [
        {
          "label": "Looks good, implement it all",
          "description": "Proceed with all 4 stages as described"
        },
        {
          "label": "Simplify Stage 2",
          "description": "Skip the encrypted flag; just having the IDOR + log leak + admin-only bulletin is enough steps"
        },
        {
          "label": "Skip the legacy hasher",
          "description": "The other red herrings are enough; a second hasher might be too much noise"
        },
        {
          "label": "I have specific feedback",
          "description": "I'll type out what I want changed"
        }
      ]
    },
    {
      "question": "For the flag location, which approach do you prefer?",
      "header": "Flag placement",
      "options": [
        {
          "label": "Encrypted in classified bulletin (Recommended)",
          "description": "Requires recovering the actual admin password to decrypt, maximum difficulty"
        },
        {
          "label": "Plaintext in classified bulletin",
          "description": "Only requires IDOR as admin; log leak + auth bypass is the main challenge"
        },
        {
          "label": "In admin user's profile field",
          "description": "Must fully compromise admin account; no IDOR needed, just straight auth bypass"
        }
      ]
    }
  ]
}
```

**Output:**

```
User has answered your questions: "How does this plan look overall? Any stages you'd want to drop, simplify, or emphasize more?"="Looks good, implement it all", "For the flag location, which approach do you prefer?"="Encrypted in classified bulletin (Recommended)". You can now continue with the user's answers in mind.
```

---

## Assistant (Plan · claude-opus-4.6 · 74.9s)

Let me finalize the plan with a few remaining details before implementation.

**Tool: question**

**Input:**

```json
{
  "questions": [
    {
      "header": "Flag format",
      "options": [
        {
          "description": "I'll tell you the exact flag string to use",
          "label": "Specific flag value"
        },
        {
          "description": "Use a placeholder like FLAG{example_flag_here} that can be replaced later",
          "label": "Placeholder flag"
        }
      ],
      "question": "What flag string should be in the encrypted classified bulletin?"
    },
    {
      "header": "Admin credentials",
      "options": [
        {
          "description": "e.g. admin/SpartanII-117-Sierra (thematic, moderately hard to guess)",
          "label": "Thematic password"
        },
        {
          "description": "Something strong that must be recovered through the log leak, not guessed",
          "label": "Strong random-ish password"
        }
      ],
      "question": "What should the admin account's credentials be? The password needs to be recoverable via the log leak + MD5 reversal path."
    },
    {
      "header": "Existing tests",
      "options": [
        {
          "description": "Update tests to match the refactored code",
          "label": "Yes, update tests (Recommended)"
        },
        {
          "description": "I'll handle tests separately",
          "label": "Skip test updates"
        }
      ],
      "question": "Should I update the existing test suite in tests/authentication/test_hasher.py to work with the refactored code?"
    },
    {
      "header": "Diagnostics discovery",
      "options": [
        {
          "description": "A non-classified bulletin mentions 'system diagnostics at /api/system/diagnostics/' in-character",
          "label": "Hint in a public bulletin"
        },
        {
          "description": "Listed in robots.txt as a Disallow entry",
          "label": "robots.txt disallow"
        },
        {
          "description": "Both a bulletin hint and robots.txt",
          "label": "Both (Recommended)"
        }
      ],
      "question": "How should players discover the diagnostics endpoint that leaks the logs?"
    }
  ]
}
```

**Output:**

```
User has answered your questions: "What flag string should be in the encrypted classified bulletin?"="Placeholder flag", "What should the admin account's credentials be? The password needs to be recoverable via the log leak + MD5 reversal path."="Strong random-ish password", "Should I update the existing test suite in tests/authentication/test_hasher.py to work with the refactored code?"="Yes, update tests (Recommended)", "How should players discover the diagnostics endpoint that leaks the logs?"="Both (Recommended)". You can now continue with the user's answers in mind.
```
