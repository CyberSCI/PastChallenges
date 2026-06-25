"""
solve.py - CyberKinz challenge solver

key0.txt is the factory test card. Its plaintext is fully documented in
cyberkinz_manual.txt. XOR key0 against that known plaintext recovers the
complete RC4 keystream, which decrypts all other cards.

Dependencies: none (pure Python 3)
Usage:
    python solve.py <host> <port>
"""

import socket
import sys

RELEASE_DIR = "../release_files"

# Factory test card plaintext - documented in cyberkinz_manual.txt
LABEL_PET    = b"PET_NAME......: "
LABEL_USER   = b"USERNAME......: "
LABEL_PASS   = b"PASSWORD......: "
LABEL_SERIAL = b"SERIAL........: "
LABEL_ISSUED = b"ISSUED........: "
W = 16   # field value width

TEST_CARD = (
    b"CYBERKINZ_REGISTRATION_CARD_v1\n"
    + LABEL_PET    + b"FACTORY_TEST    " + b"\n"
    + LABEL_USER   + b"TESTUSER        " + b"\n"
    + LABEL_PASS   + b"TESTPASS        " + b"\n"
    + LABEL_SERIAL + b"0000000000000000" + b"\n"
    + LABEL_ISSUED + b"2025-01-01"       + b"\n"
    + b"END_OF_RECORD\n"
)

def xor_bytes(a, b):
    return bytes(x ^ y for x, y in zip(a, b))

def load_hex(path):
    with open(path) as f:
        return bytes.fromhex(f.read().strip())

def parse_card(plaintext):
    fields = {}
    for line in plaintext.decode(errors="replace").splitlines():
        if ": " in line:
            label, value = line.split(": ", 1)
            fields[label.rstrip(".")] = value.strip()
    return fields

def login(host, port, username, password):
    with socket.create_connection((host, port), timeout=10) as s:
        f = s.makefile("rwb", buffering=0)
        buf = b""
        while not buf.endswith(b"Username: "):
            buf += f.read(1)
        f.write((username + "\n").encode())
        f.flush()
        buf = b""
        while not buf.endswith(b"Password: "):
            buf += f.read(1)
        f.write((password + "\n").encode())
        f.flush()
        return f.read(512).decode(errors="replace")

def main():
    if len(sys.argv) != 3:
        print(f"Usage: python {sys.argv[0]} <host> <port>")
        sys.exit(1)

    host = sys.argv[1]
    port = int(sys.argv[2])

    c0 = load_hex(f"{RELEASE_DIR}/key0.txt")
    c1 = load_hex(f"{RELEASE_DIR}/key1.txt")
    c2 = load_hex(f"{RELEASE_DIR}/key2.txt")
    c3 = load_hex(f"{RELEASE_DIR}/key3.txt")

    print("[*] Recovering keystream from factory test card (key0)...")
    print(f"[*] Ciphertext (key0): {c0.hex()}")
    keystream = xor_bytes(c0, TEST_CARD)
    print(f"[*] Keystream: {keystream.hex()}")

    cards = []
    for i, ct in enumerate([c1, c2, c3], 1):
        pt = xor_bytes(ct, keystream)
        fields = parse_card(pt)
        user = fields.get("USERNAME", "").strip()
        pwd  = fields.get("PASSWORD", "").strip()
        print(f"[*] Card {i}: USERNAME={user!r}  PASSWORD={pwd!r}")
        if user and pwd:
            cards.append((user, pwd))

    print(f"\n[*] Trying {len(cards)} credential set(s) against {host}:{port} ...")
    for user, pwd in cards:
        print(f"[*] Trying {user!r} / {pwd!r}")
        try:
            response = login(host, port, user, pwd)
            if "LOGIN OK" in response or "cybersci{" in response:
                print(f"[+] Success!\n{response}")
                return
            print(f"    -> {response.strip()}")
        except Exception as e:
            print(f"    -> Error: {e}")

    print("[-] No valid credentials found.")

if __name__ == "__main__":
    main()
