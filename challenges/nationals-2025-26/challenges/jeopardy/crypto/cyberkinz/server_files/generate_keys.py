"""
generate_keys.py - produce key0.txt, key1.txt, key2.txt, key3.txt

All four registration cards are RC4-encrypted under the SAME batch key
(the "broken factory RNG" bug).

key0.txt is the factory test card - its plaintext is fully documented in
cyberkinz_manual.txt. Players XOR any key against key0 to recover the
complete RC4 keystream, then decrypt all other cards.

Dependencies: pycryptodome
    pip install pycryptodome
Usage:
    python generate_keys.py
"""

import os
from Crypto.Cipher import ARC4

RELEASE_DIR = os.path.join(os.path.dirname(__file__), "../release_files")
SECRET_PATH = os.path.join(os.path.dirname(__file__), "secret.txt")

FLAG        = "cybersci{r3us3d_k3ys_ar3_n0_k3ys-360163}"
VALID_USER  = "alpha_unit"
VALID_PASS  = "WYj>+#HiF4TU3a.m"

LABEL_PET    = b"PET_NAME......: "
LABEL_USER   = b"USERNAME......: "
LABEL_PASS   = b"PASSWORD......: "
LABEL_SERIAL = b"SERIAL........: "
LABEL_ISSUED = b"ISSUED........: "
FIELD_WIDTH  = 16
DATE_WIDTH   = 10

def build_card(pet, user, pwd, serial, issued):
    assert len(pet)    <= FIELD_WIDTH, f"pet name too long: {pet!r}"
    assert len(user)   <= FIELD_WIDTH, f"username too long: {user!r}"
    assert len(pwd)    <= FIELD_WIDTH, f"password too long: {pwd!r}"
    assert len(serial) <= FIELD_WIDTH, f"serial too long: {serial!r}"
    assert len(issued) == DATE_WIDTH,  f"date must be YYYY-MM-DD: {issued!r}"

    return (
        b"CYBERKINZ_REGISTRATION_CARD_v1\n"
        + LABEL_PET    + pet.ljust(FIELD_WIDTH).encode()    + b"\n"
        + LABEL_USER   + user.ljust(FIELD_WIDTH).encode()   + b"\n"
        + LABEL_PASS   + pwd.ljust(FIELD_WIDTH).encode()    + b"\n"
        + LABEL_SERIAL + serial.ljust(FIELD_WIDTH).encode() + b"\n"
        + LABEL_ISSUED + issued.encode()                    + b"\n"
        + b"END_OF_RECORD\n"
    )

# Factory test card - plaintext is publicly documented in cyberkinz_manual.txt.
# Gives players the full RC4 keystream once XOR'd against key0.txt.
P0 = build_card("FACTORY_TEST", "TESTUSER", "TESTPASS", "0000000000000000", "2025-01-01")

# Card 1: flag-bearing account
P1 = build_card("Sparky",  VALID_USER, VALID_PASS, "DEADBEEFCAFEBABE", "2025-08-14")
# Card 2: decoy
P2 = build_card("Bitsy",   "beta_unit",  "bartertown99",   "FEEDFACE12345678", "2025-09-02")
# Card 3: decoy registered to viper92 (cross-challenge narrative breadcrumb)
P3 = build_card("Glitch",  "viper92",    "scr4p_m3t4l_99", "BADC0FFEE0DDF00D", "2025-09-19")

assert len(P0) == len(P1) == len(P2) == len(P3), "Record lengths differ - byte offsets will not align"
print(f"Record length: {len(P0)} bytes")

# ---------------------------------------------------------------------------
# Encrypt all four under the same batch key
# ---------------------------------------------------------------------------

BATCH_KEY = os.urandom(16)

C0 = ARC4.new(BATCH_KEY).encrypt(P0).hex()
C1 = ARC4.new(BATCH_KEY).encrypt(P1).hex()
C2 = ARC4.new(BATCH_KEY).encrypt(P2).hex()
C3 = ARC4.new(BATCH_KEY).encrypt(P3).hex()

# ---------------------------------------------------------------------------
# Write output files
# ---------------------------------------------------------------------------

os.makedirs(RELEASE_DIR, exist_ok=True)

for fname, ct in [("key0.txt", C0), ("key1.txt", C1), ("key2.txt", C2), ("key3.txt", C3)]:
    path = os.path.join(RELEASE_DIR, fname)
    with open(path, "w") as f:
        f.write(ct + "\n")
    print(f"Written: {path}")

with open(SECRET_PATH, "w") as f:
    f.write(f"BATCH_KEY={BATCH_KEY.hex()}\n")
    f.write(f"FLAG={FLAG}\n")
    f.write(f"VALID_USER={VALID_USER}\n")
    f.write(f"VALID_PASS={VALID_PASS}\n")
    f.write(f"P0={P0!r}\n")
    f.write(f"P1={P1!r}\n")
    f.write(f"P2={P2!r}\n")
    f.write(f"P3={P3!r}\n")
print(f"Written: {SECRET_PATH}")

# ---------------------------------------------------------------------------
# Self-verification: confirm key0 anchor gives full keystream recovery
# ---------------------------------------------------------------------------

def xor_bytes(a, b):
    return bytes(x ^ y for x, y in zip(a, b))

c0 = bytes.fromhex(C0)
c1 = bytes.fromhex(C1)
c2 = bytes.fromhex(C2)
c3 = bytes.fromhex(C3)

# Keystream = C0 XOR P0 (P0 is fully known from the manual)
keystream = xor_bytes(c0, P0)

assert xor_bytes(c1, keystream) == P1, "P1 recovery failed"
assert xor_bytes(c2, keystream) == P2, "P2 recovery failed"
assert xor_bytes(c3, keystream) == P3, "P3 recovery failed"
print("Self-check passed: key0 anchor recovers all three plaintexts.")
