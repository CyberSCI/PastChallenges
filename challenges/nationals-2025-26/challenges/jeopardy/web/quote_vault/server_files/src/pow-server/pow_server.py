#!/usr/bin/env python3
"""ocr-rotator proof-of-work proxy.

Two-step PoW flow:

  1. Get the current challenge for the image you want:

         GET /pow/challenge?image=<filename>
         → {"challenge": "<32 hex chars>", "image": "<filename>", "bits": 18}

     The challenge rotates every 50 seconds (matches the data rotation).

  2. Find a nonce string such that

         sha256(challenge + image_filename + nonce)

     has at least `bits` leading zero bits.

  3. Submit the solved nonce so the proxy registers it as active:

         POST /pow/submit
         Content-Type: application/json
         {"image": "<filename>", "nonce": "<nonce>"}

     → {"ok": true}

     A 60-second TTL applies; nonces older than that are dropped.

  4. Fetch the image with the registered nonce:

         GET /images/<filename>?pow=<nonce>      (or X-PoW-Nonce header)

     A request whose nonce isn't currently registered returns 403.
"""

import hashlib
import http.server
import json
import os
import posixpath
import re
import threading
import time
import urllib.error
import urllib.parse
import urllib.request

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

POW_BITS: int = 18              # 2^18 ≈ 260k attempts (~3-8s in browser, ~120ms in C)
ROTATION_INTERVAL: int = 50     # must match generator.py
NONCE_TTL: int = 60             # seconds an active nonce remains valid after submit
UPSTREAM: str = "http://127.0.0.1:8081"

# Per-image GETs are gated. The autoindex (/images/) is forwarded
# unchanged so players can scrape the listing freely — bottleneck is the
# 5000 individual fetches.
_GATED_PATH = re.compile(r"^/images/img-\d{5}\.png$")
_SUBMITTABLE_IMAGE = re.compile(r"^img-\d{5}\.png$")

# When the proxy detects a nonce being reused for a *different* filename
# than the one it was originally registered for (the replay bypass), it
# still serves the image (that's the bug) but tags the response with this
# header. The flag value is the header content.
REPLAY_FLAG_HEADER = "X-Audit-Token"
REPLAY_FLAG = "Cybersci{pow-replay-bypass-K2pV7m}"

# ---------------------------------------------------------------------------
# Challenge — derived from the current 50-s slot, no coordination needed
# ---------------------------------------------------------------------------

def _slot_challenge(slot: int) -> str:
    return hashlib.sha256(str(slot).encode()).hexdigest()[:32]


def current_challenge() -> str:
    return _slot_challenge(int(time.time()) // ROTATION_INTERVAL)


def valid_challenges() -> list[str]:
    """Accept the current and the previous slot so submissions made near a
    rotation edge survive the cutover."""
    slot = int(time.time()) // ROTATION_INTERVAL
    return [_slot_challenge(slot), _slot_challenge(slot - 1)]

# ---------------------------------------------------------------------------
# PoW validation (used at submit time)
# ---------------------------------------------------------------------------

def _leading_zero_bits_ok(digest: bytes, bits: int) -> bool:
    full_bytes, remainder = divmod(bits, 8)
    if any(digest[i] for i in range(full_bytes)):
        return False
    if remainder and (digest[full_bytes] >> (8 - remainder)):
        return False
    return True


def validate_pow(image: str, nonce: str) -> bool:
    """sha256(challenge + image + nonce) must have POW_BITS leading zeros.
    Either the current or the previous slot's challenge is accepted.
    """
    for ch in valid_challenges():
        digest = hashlib.sha256(f"{ch}{image}{nonce}".encode()).digest()
        if _leading_zero_bits_ok(digest, POW_BITS):
            return True
    return False

# ---------------------------------------------------------------------------
# Active-nonce table  (the place where the bug lives)
#
# We track {nonce: {"filename": str, "expiry": float}}. The structure
# stores the filename the nonce was submitted for — but the *retrieval*
# path only checks that the nonce is in the table, not whether the
# entry's filename matches the image being requested. A real-world
# forgotten-check class of bug; with this in place a player who
# submits a nonce for image A can use it to fetch image B.
# ---------------------------------------------------------------------------

_NONCE_LOCK = threading.Lock()
_ACTIVE_NONCES: dict[str, dict] = {}


def _expire_locked() -> None:
    now = time.time()
    expired = [k for k, v in _ACTIVE_NONCES.items() if v["expiry"] < now]
    for k in expired:
        del _ACTIVE_NONCES[k]


def register_nonce(nonce: str, filename: str) -> None:
    with _NONCE_LOCK:
        _expire_locked()
        _ACTIVE_NONCES[nonce] = {
            "filename": filename,
            "expiry": time.time() + NONCE_TTL,
        }


def lookup_nonce(nonce: str):
    """Return the entry, or None if expired/missing."""
    with _NONCE_LOCK:
        _expire_locked()
        return _ACTIVE_NONCES.get(nonce)


# ---------------------------------------------------------------------------
# Static response bodies
# ---------------------------------------------------------------------------

_403_BODY = json.dumps({
    "error": "proof-of-work required",
    "how": [
        "GET /pow/challenge?image=<filename> to obtain the current challenge",
        "find nonce so sha256(challenge + image + nonce) has 18 leading zero bits",
        "POST /pow/submit with {image, nonce} to register the nonce",
        "retry with ?pow=<nonce> or X-PoW-Nonce: <nonce>",
    ],
}, indent=2).encode()


def _send(handler: http.server.BaseHTTPRequestHandler, code: int,
          content_type: str, body: bytes) -> None:
    handler.send_response(code)
    handler.send_header("Content-Type", content_type)
    handler.send_header("Content-Length", str(len(body)))
    handler.end_headers()
    handler.wfile.write(body)


# ---------------------------------------------------------------------------
# HTTP handler
# ---------------------------------------------------------------------------

class PowHandler(http.server.BaseHTTPRequestHandler):

    def _path(self) -> str:
        """Percent-decoded, normalised path. Collapses repeated slashes and
        resolves "." / ".." segments so the gate sees the same path that
        the upstream resolver (nginx) would after its own normalisation —
        no `//img-…` bypass via `merge_slashes on`."""
        raw = urllib.parse.urlparse(self.path).path
        decoded = urllib.parse.unquote(raw) if raw else "/"
        had_trailing_slash = decoded != "/" and decoded.endswith("/")
        normed = posixpath.normpath(decoded)
        # posixpath.normpath collapses leading "//" to "/" except when there
        # are exactly two leading slashes (POSIX edge case). Force "/" prefix.
        if not normed.startswith("/"):
            normed = "/" + normed
        # normpath strips trailing slashes; restore so directory routes
        # like `/images/` (autoindex) keep matching nginx's location block.
        if had_trailing_slash and not normed.endswith("/"):
            normed += "/"
        return normed

    def _query(self) -> dict:
        return urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)

    def _normalised_request_target(self) -> str:
        """The path-and-query that proxy()/upstream should see — matches
        what _path() returned, plus any query string from the original URL.
        Path is re-percent-encoded so urllib can build a valid URL even
        when the decoded path contains spaces, quotes, or other reserved
        characters (typical of the GraphQL-injected /api/quotes/<…> paths)."""
        clean = self._path()
        query = urllib.parse.urlparse(self.path).query
        encoded = urllib.parse.quote(clean, safe="/")
        return encoded + ("?" + query if query else "")

    def do_GET(self):
        clean = self._path()
        if clean == "/pow/challenge":
            self._handle_challenge()
        elif _GATED_PATH.match(clean):
            self._handle_image(clean)
        else:
            self._proxy()

    def do_POST(self):
        clean = self._path()
        if clean == "/pow/submit":
            self._handle_submit()
        else:
            self._proxy()

    def do_OPTIONS(self):
        # Be permissive enough that the static frontend can POST /pow/submit
        # without a CORS preflight failure if anything ever moves cross-origin.
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, X-PoW-Nonce")
        self.send_header("Content-Length", "0")
        self.end_headers()

    def do_HEAD(self):
        _send(self, 405, "application/json", b'{"error":"method not allowed"}')

    # ---- /pow/challenge ----------------------------------------------------

    def _handle_challenge(self):
        image = self._query().get("image", [""])[0]
        body = json.dumps({
            "challenge": current_challenge(),
            "image": image,
            "bits": POW_BITS,
        }, indent=2).encode()
        _send(self, 200, "application/json", body)

    # ---- /pow/submit -------------------------------------------------------

    def _handle_submit(self):
        try:
            length = int(self.headers.get("Content-Length", "0") or "0")
            raw = self.rfile.read(length).decode("utf-8") if length > 0 else "{}"
            data = json.loads(raw)
        except (ValueError, json.JSONDecodeError):
            _send(self, 400, "application/json",
                  b'{"error":"bad request body"}')
            return
        image = data.get("image")
        nonce = data.get("nonce")
        if not isinstance(image, str) or not isinstance(nonce, str) or not image or not nonce:
            _send(self, 400, "application/json",
                  b'{"error":"missing or non-string image / nonce"}')
            return
        # Submissions are only accepted for actual card images.
        if not _SUBMITTABLE_IMAGE.match(image):
            _send(self, 400, "application/json",
                  b'{"error":"image must be a card filename like img-NNNNN.png"}')
            return
        if not validate_pow(image, nonce):
            _send(self, 403, "application/json",
                  b'{"error":"proof-of-work invalid"}')
            return
        register_nonce(nonce, image)
        _send(self, 200, "application/json", b'{"ok":true}')

    # ---- /images/<filename> -----------------------------------------------

    def _handle_image(self, clean_path: str):
        nonce = self._query().get("pow", [""])[0]
        if not nonce:
            nonce = self.headers.get("X-PoW-Nonce", "")
        if not nonce:
            _send(self, 403, "application/json", _403_BODY)
            return
        # The "forgotten check": we only verify the nonce is registered,
        # not that it was registered for *this* filename.
        entry = lookup_nonce(nonce)
        if entry is None:
            _send(self, 403, "application/json", _403_BODY)
            return

        # Replay detection. If the nonce is being used for a different
        # filename than the one it was registered for, we still serve the
        # image (that's the bug) but tag the response with the audit
        # header so attentive players spot the silent flag.
        requested_file = clean_path.rsplit('/', 1)[-1]
        extras = {}
        if entry.get("filename") != requested_file:
            extras[REPLAY_FLAG_HEADER] = REPLAY_FLAG
        self._proxy(extra_response_headers=extras)

    # ---- everything else: transparent proxy to nginx -----------------------

    def _proxy(self, extra_response_headers=None):
        extras = extra_response_headers or {}
        try:
            # Forward the *normalised* request target so the upstream sees
            # the same path the gate matched against. Stops the
            # "double-slash bypass" where nginx's merge_slashes rewrites
            # `/images//img-X.png` back to `/images/img-X.png` after the
            # regex check has decided it's not an image path.
            url = UPSTREAM + self._normalised_request_target()
            req = urllib.request.Request(url, method=self.command)
            for h, v in self.headers.items():
                if h.lower() in {"host", "content-length", "transfer-encoding"}:
                    continue
                req.add_header(h, v)
            body_in = None
            if self.command == "POST":
                length = int(self.headers.get("Content-Length", "0") or "0")
                body_in = self.rfile.read(length) if length > 0 else b""
            with urllib.request.urlopen(req, data=body_in, timeout=15) as r:
                body = r.read()
                self.send_response(r.status)
                skip = {"transfer-encoding", "connection", "content-length"}
                for k, v in r.headers.items():
                    if k.lower() not in skip:
                        self.send_header(k, v)
                for k, v in extras.items():
                    self.send_header(k, v)
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)
        except urllib.error.HTTPError as e:
            try:
                body = e.read()
            except Exception:
                body = b""
            self.send_response(e.code)
            for k, v in e.headers.items():
                if k.lower() not in {"transfer-encoding", "connection", "content-length"}:
                    self.send_header(k, v)
            for k, v in extras.items():
                self.send_header(k, v)
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        except Exception:
            self.send_response(502)
            self.end_headers()

    def log_message(self, *_args) -> None:
        pass


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    port = int(os.environ.get("POW_PORT", "8080"))
    server = http.server.ThreadingHTTPServer(("0.0.0.0", port), PowHandler)
    server.serve_forever()
