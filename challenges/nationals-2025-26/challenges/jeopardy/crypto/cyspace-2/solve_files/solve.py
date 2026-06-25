"""
solve.py - CySpace.com Part II solver

Recovers @viper92's DSA private key via nonce reuse, forges a signed
inbox-access request, and retrieves the flag from the server.

Dependencies: none (pure Python 3.8+)
Usage:
    python solve.py <host> <port>
"""

import hashlib
import json
import secrets
import socket
import sys
import time

RELEASE_DIR = "../release_files"

# ---------------------------------------------------------------------------
# Load challenge files
# ---------------------------------------------------------------------------

def load_posts():
    with open(f"{RELEASE_DIR}/cyspace_posts.json") as f:
        return json.load(f)

def load_params():
    ns = {}
    exec(open(f"{RELEASE_DIR}/cyspace_params.py").read(), ns)
    return ns["p"], ns["q"], ns["g"], ns["y"]

# ---------------------------------------------------------------------------
# DSA helpers
# ---------------------------------------------------------------------------

def sha1_int(data: bytes) -> int:
    return int(hashlib.sha1(data).hexdigest(), 16)

def make_envelope(post_id, timestamp, author, body) -> bytes:
    return f"{post_id}|{timestamp}|@{author}|{body}".encode("utf-8")

def dsa_sign(h, x, q, g, p, k):
    r = pow(g, k, p) % q
    s = pow(k, -1, q) * (h + x * r) % q
    return r, s

# ---------------------------------------------------------------------------
# Step 1: find the duplicate-r pair
# ---------------------------------------------------------------------------

def find_nonce_reuse(posts):
    seen = {}
    for post in posts:
        r = post["r"]
        if r in seen:
            return seen[r], post
        seen[r] = post
    raise ValueError("No duplicate r found - is this the right posts file?")

# ---------------------------------------------------------------------------
# Step 2: recover k and private key x
# ---------------------------------------------------------------------------

def recover_private_key(post_a, post_b, q, g, p, y):
    env_a = make_envelope(post_a["post_id"], post_a["timestamp"],
                          post_a["author"],  post_a["body"])
    env_b = make_envelope(post_b["post_id"], post_b["timestamp"],
                          post_b["author"],  post_b["body"])

    h1 = sha1_int(env_a)
    h2 = sha1_int(env_b)
    s1 = post_a["s"]
    s2 = post_b["s"]
    r  = post_a["r"]
    assert r == post_b["r"], "r values differ - check find_nonce_reuse"

    # k = (h1 - h2) * modinv(s1 - s2, q) mod q
    k = (h1 - h2) * pow(s1 - s2, -1, q) % q

    # x = (s1*k - h1) * modinv(r, q) mod q
    x = (s1 * k - h1) * pow(r, -1, q) % q

    if pow(g, x, p) != y:
        raise ValueError(
            "Key recovery failed: pow(g, x, p) != y.\n"
            "The envelope reconstruction may be wrong - check the field format in cyspace_api.txt."
        )

    return x, k

# ---------------------------------------------------------------------------
# Step 3: forge a signed inbox-access envelope
# ---------------------------------------------------------------------------

def forge_inbox_request(x, q, g, p):
    request_id = "INBOX-" + secrets.token_hex(4)
    ts         = int(time.time())
    body       = "INBOX_REQUEST"
    env        = make_envelope(request_id, ts, "viper92", body)
    h          = sha1_int(env)

    k_new = secrets.randbelow(q - 1) + 1
    r_new, s_new = dsa_sign(h, x, q, g, p, k_new)

    return env.decode("utf-8"), r_new, s_new

# ---------------------------------------------------------------------------
# Step 4: connect and retrieve the flag
# ---------------------------------------------------------------------------

def get_flag(host, port, envelope_str, r, s):
    with socket.create_connection((host, port), timeout=15) as conn:
        f = conn.makefile("rwb", buffering=0)

        # Read banner up to "> " prompt
        buf = b""
        while not buf.endswith(b"> "):
            chunk = f.read(1)
            if not chunk:
                break
            buf += chunk

        # Send envelope, r, s
        f.write((envelope_str + "\n").encode())
        f.write(f"r={r}\n".encode())
        f.write(f"s={s}\n".encode())
        f.flush()

        # Read full response
        response = b""
        conn.settimeout(3.0)
        try:
            while True:
                chunk = f.read(512)
                if not chunk:
                    break
                response += chunk
        except (socket.timeout, OSError):
            pass

        return response.decode(errors="replace")

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    if len(sys.argv) != 3:
        print(f"Usage: python {sys.argv[0]} <host> <port>")
        sys.exit(1)

    host = sys.argv[1]
    port = int(sys.argv[2])

    print("[*] Loading posts and DSA parameters...")
    posts        = load_posts()
    p, q, g, y  = load_params()
    print(f"    {len(posts)} posts loaded. q={q.bit_length()}-bit, p={p.bit_length()}-bit.")

    print("[*] Scanning for duplicate r (nonce reuse)...")
    post_a, post_b = find_nonce_reuse(posts)
    print(f"    Found: posts {post_a['post_id']} and {post_b['post_id']} share r={str(post_a['r'])}")

    print("[*] Recovering private key x...")
    x, k = recover_private_key(post_a, post_b, q, g, p, y)
    print(f"    pow(g, x, p) == y: {pow(g, x, p) == y}  [checkpoint passed]")

    print("[*] Forging signed inbox-access request...")
    env_str, r_new, s_new = forge_inbox_request(x, q, g, p)
    print(f"    Envelope: {env_str}")

    print(f"[*] Connecting to {host}:{port}...")
    response = get_flag(host, port, env_str, r_new, s_new)

    if "VERIFICATION FAILED" in response:
        print("[-] Signature rejected by server.")
        print(response)
    else:
        print("[+] Success!")
        print(response)

if __name__ == "__main__":
    main()
