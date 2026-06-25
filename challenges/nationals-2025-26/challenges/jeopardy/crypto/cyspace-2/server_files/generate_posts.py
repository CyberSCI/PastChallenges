"""
generate_posts.py - produce cyspace_posts.json, cyspace_params.py, secret.txt

Generates FIPS 186-1 DSA parameters, signs ~50 posts, deliberately reuses
the nonce k on two non-adjacent posts, and writes all output files.

Dependencies: sympy
    pip install sympy
Usage:
    python generate_posts.py
"""

import hashlib
import json
import os
import random
import secrets
import sys
import textwrap
import time

from sympy import isprime, nextprime

RELEASE_DIR = os.path.join(os.path.dirname(__file__), "../release_files")
SECRET_PATH = os.path.join(os.path.dirname(__file__), "secret.txt")

FLAG   = "cybersci{s4me_k_tw1ce_1s_n0_s3cr3t_959463}"
AUTHOR = "viper92"
N_POSTS = 50

# ---------------------------------------------------------------------------
# DSA parameter generation - FIPS 186-1 style (1024-bit p, 160-bit q)
# ---------------------------------------------------------------------------

def gen_prime_q(bits=160):
    """Random prime of exactly `bits` bits."""
    while True:
        q = secrets.randbits(bits) | (1 << (bits - 1)) | 1
        if isprime(q):
            return q

def gen_prime_p(q, bits=1024):
    """Find a prime p of `bits` bits such that q | (p-1)."""
    while True:
        # p = k*q + 1 for some k
        k = secrets.randbits(bits - 160) | (1 << (bits - 161))
        k = k - (k % 2)          # make k even so p is odd
        p = k * q + 1
        if p.bit_length() == bits and isprime(p):
            return p

def gen_generator(p, q):
    """Find a generator g of the unique subgroup of order q in Z*_p."""
    while True:
        h = random.randint(2, p - 2)
        g = pow(h, (p - 1) // q, p)
        if g > 1:
            return g

def gen_dsa_params():
    print("Generating DSA parameters (1024-bit p, 160-bit q) - this may take ~30s...")
    q = gen_prime_q(160)
    p = gen_prime_p(q, 1024)
    g = gen_generator(p, q)
    x = secrets.randbelow(q - 1) + 1   # private key
    y = pow(g, x, p)                   # public key
    assert pow(g, x, p) == y
    print(f"  q = {q.bit_length()}-bit prime")
    print(f"  p = {p.bit_length()}-bit prime,  q | (p-1): {(p-1) % q == 0}")
    print(f"  g order check: pow(g,q,p)==1: {pow(g, q, p) == 1}")
    return p, q, g, x, y

# ---------------------------------------------------------------------------
# DSA sign / verify
# ---------------------------------------------------------------------------

def dsa_sign(h, x, q, g, p, k):
    r = pow(g, k, p) % q
    s = pow(k, -1, q) * (h + x * r) % q
    assert r != 0 and s != 0
    return r, s

def dsa_verify(h, r, s, y, q, g, p):
    if not (0 < r < q and 0 < s < q):
        return False
    w  = pow(s, -1, q)
    u1 = h * w % q
    u2 = r * w % q
    v  = (pow(g, u1, p) * pow(y, u2, p) % p) % q
    return v == r

def envelope(post_id, timestamp, author, body):
    return f"{post_id}|{timestamp}|@{author}|{body}".encode("utf-8")

def sha1_int(data: bytes) -> int:
    return int(hashlib.sha1(data).hexdigest(), 16)

# ---------------------------------------------------------------------------
# Post bodies - period-accurate early-social-network + post-EMP world
# ---------------------------------------------------------------------------

BODIES = [
    "CYBERSPACE IS BACK. first post. never thought i'd see this again",
    "found a working 486 in the rubble downtown. she boots :)",
    "trading: 28.8 baud modem + power supply. want: canned food or batteries. DM me",
    "anyone else getting packet loss on the eastern backbone? constant dropouts since tuesday",
    "lol my CyberKinz is still alive. glitch survived the EMP on a dead battery somehow",
    "the radio tower on mont-royal is back. picked up a signal last night. not sure who",
    "reminder: DO NOT use WEP. yes i know it's the only option on the salvaged APs. still no",
    "hot take: dial-up is actually fine. we built this network on vibes and phone line",
    "cyberspace feels different now. quieter. miss the spam honestly",
    "got a sun sparc running again. she's slow but she's mine",
    "posting from a public terminal at the library. it's a 386. life is good",
    "anyone remember geocities? asking for a friend (me). trying to rebuild my page",
    "the EMP took everything but the Tamagotchis somehow survived. the cockroaches of tech",
    "signal analysis on the eastern dial-up relay is showing anomalies. not natural noise",
    "new rule: all comms signed. if it doesn't have a sig i don't trust it. FIPS 186 or bust",
    "happy to report CySpace.com is back. the 1999 codebase is running on a pentium II",
    "found a cache of ZIP disks in a storage unit. contents: mostly memes. worth it",
    "there are people out there using the network for things they shouldn't. stay safe",
    "tip: if you're on a salvaged dial-up line, check your connection recording for anomalies",
    "the remnant is real. i've seen the traffic. encrypted but the pattern is there",
    "scored a laser printer at the old university. toner cartridges are gold right now",
    "remember when we complained about 56k? i would kill for 56k right now",
    "first time checking messages in 3 days. the aol session cut out twice. worth it",
    "does anyone have a patch for the 1999 SSL vuln or are we all just living dangerously",
    "finally got PGP working on the salvaged thinkpad. took a week. no regrets",
    "the latency on this connection is something else. 1200ms ping. classic",
    "shoutout to whoever is keeping the usenet backbone alive. you are a hero",
    "running apache 1.3 on a rescued pentium MMX. it's fine. everything is fine",
    "if anyone has a copy of netscape 4 on floppies please DM me immediately",
    "just found out the library has a gopher server. going back to 1993 i guess",
    "power grid section C is back. that means three more relay nodes are online",
    "someone is scanning the entire 10.0.0.0/8 range. don't know who. watching it",
    "wrote a perl script to monitor the modem line. found something weird in the noise",
    "trading a working serial mouse for literally anything useful. please",
    "the ham radio operators deserve more credit. they kept us connected when nothing else worked",
    "old crypto is everywhere now. DES, RC4, MD5. the auditors are gonna have a field day",
    "DM me if you need help getting your old PC online. done 12 setups this month",
    "CySpace is growing fast. saw 80 users online last night. record since the EMP",
    "can't stop thinking about how we took 100mbps for granted. unreal",
    "new post coming soon. been compiling intel. things are moving out there",
    "the packet headers on the eastern relay look manually crafted. someone knows what they're doing",
    "anyone else notice the dial-up traffic spike at 03:00 UTC every night? not random",
    "keeping my head down. less said the better. stay safe out there",
    "if you're reading this, the network is still up. small victories",
    "upgraded the modem from 14.4 to 33.6. felt like installing fibre. incredible",
    "the remnant doesn't make mistakes twice. keep your keys rotated",
    "three different IPs hit my gopher server in the last hour. unusual",
    "someone left a ZIP disk in the public terminal. it had a key on it. reported it",
    "comms discipline matters. sign everything. verify everything. trust nothing",
    "last message for a while. going dark. you know why",
]

assert len(BODIES) >= N_POSTS, "not enough post bodies"

# ---------------------------------------------------------------------------
# Generate posts
# ---------------------------------------------------------------------------

def generate_posts(p, q, g, x):
    rng = random.Random(42)   # seeded for reproducibility of order/timestamps
    bodies = rng.sample(BODIES, N_POSTS)

    # Timestamps: monotonically increasing, spread over ~3 months post-EMP
    base_ts = 1751673600   # 2025-07-05 00:00:00 UTC (post-EMP world)
    timestamps = sorted(rng.randint(base_ts, base_ts + 90 * 86400)
                        for _ in range(N_POSTS))

    # Choose two non-adjacent indices for nonce reuse
    i_a = rng.randint(5, 20)
    i_b = rng.randint(30, 45)
    assert abs(i_a - i_b) > 5

    k_reused = secrets.randbelow(q - 1) + 1

    posts = []
    for i, (body, ts) in enumerate(zip(bodies, timestamps)):
        post_id = f"{i+1:05d}"
        env     = envelope(post_id, ts, AUTHOR, body)
        h       = sha1_int(env)

        k = k_reused if i in (i_a, i_b) else (secrets.randbelow(q - 1) + 1)
        r, s = dsa_sign(h, x, q, g, p, k)

        posts.append({
            "post_id":   post_id,
            "timestamp": ts,
            "author":    AUTHOR,
            "body":      body,
            "r":         r,
            "s":         s,
        })

    return posts, i_a, i_b, k_reused

# ---------------------------------------------------------------------------
# Verification
# ---------------------------------------------------------------------------

def verify_all(posts, p, q, g, y, i_a, i_b):
    print("Verifying all signatures...")
    for post in posts:
        env = envelope(post["post_id"], post["timestamp"], post["author"], post["body"])
        h   = sha1_int(env)
        ok  = dsa_verify(h, post["r"], post["s"], y, q, g, p)
        assert ok, f"Signature invalid for post {post['post_id']}"

    assert posts[i_a]["r"] == posts[i_b]["r"], "Nonce reuse posts don't share r"
    r_values = [p["r"] for p in posts]
    dups = len(r_values) - len(set(r_values))
    assert dups == 1, f"Expected exactly 1 duplicate r, found {dups}"
    print(f"  All {len(posts)} signatures valid.")
    print(f"  Nonce reuse at posts [{i_a}] and [{i_b}] (r={posts[i_a]['r'] % 10**12}...)")
    print(f"  Exactly 1 duplicate-r pair. Check passed.")

# ---------------------------------------------------------------------------
# Write output files
# ---------------------------------------------------------------------------

def write_params(p, q, g, y):
    path = os.path.join(RELEASE_DIR, "cyspace_params.py")
    with open(path, "w") as f:
        f.write("# CySpace.com DSA domain parameters - FIPS 186-1 (1994)\n")
        f.write("# Hash function: SHA-1 (FIPS 180-1, 1995)\n")
        f.write("# Generated by generate_posts.py at build time.\n\n")
        f.write(f"p = {p}\n\n")
        f.write(f"q = {q}\n\n")
        f.write(f"g = {g}\n\n")
        f.write(f"y = {y}  # @viper92's public key\n")
    print(f"Written: {path}")

def write_posts(posts):
    path = os.path.join(RELEASE_DIR, "cyspace_posts.json")
    with open(path, "w") as f:
        json.dump(posts, f, indent=2)
    print(f"Written: {path}  ({len(posts)} posts)")

def write_secret(p, q, g, x, y, k_reused, i_a, i_b):
    with open(SECRET_PATH, "w") as f:
        f.write(f"FLAG={FLAG}\n")
        f.write(f"x={x}\n")
        f.write(f"k_reused={k_reused}\n")
        f.write(f"i_a={i_a}\n")
        f.write(f"i_b={i_b}\n")
        f.write(f"p={p}\n")
        f.write(f"q={q}\n")
        f.write(f"g={g}\n")
        f.write(f"y={y}\n")
    print(f"Written: {SECRET_PATH}")

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    os.makedirs(RELEASE_DIR, exist_ok=True)

    p, q, g, x, y = gen_dsa_params()

    print(f"Generating {N_POSTS} posts...")
    posts, i_a, i_b, k_reused = generate_posts(p, q, g, x)

    verify_all(posts, p, q, g, y, i_a, i_b)

    write_params(p, q, g, y)
    write_posts(posts)
    write_secret(p, q, g, x, y, k_reused, i_a, i_b)

    print("\nDone. Pre-deploy checklist:")
    print("  [x] pow(g, x, p) == y:", pow(g, x, p) == y)
    print(f"  [x] Nonce-reuse pair: posts[{i_a}] and posts[{i_b}]")
    print("  [x] All 50 signatures verify.")
