"""
CTF NFC dump builder
Requires: pip install pycryptodome
"""
import struct
import binascii
import hashlib
from Crypto.Cipher import AES

# ─────────────────────────────────────────
#  HELPERS
# ─────────────────────────────────────────

def pad_field(value: bytes, length: int) -> bytes:
    return value[:length].ljust(length, b'\x00')

def derive_key(name, surname, id_, gender):
    material = (
        pad_field(name, 25) +
        pad_field(surname, 25) +
        pad_field(id_, 16) +
        bytes([gender])
    )  # 67 bytes
    return hashlib.sha256(material).digest()  # 32 bytes → AES-256

def encrypt_ecb(key: bytes, plaintext: bytes) -> bytes:
    pad_len = 16 - (len(plaintext) % 16)
    plaintext += bytes([pad_len] * pad_len)
    return AES.new(key, AES.MODE_ECB).encrypt(plaintext)

def decrypt_ecb(key: bytes, ciphertext: bytes) -> bytes:
    plaintext = AES.new(key, AES.MODE_ECB).decrypt(ciphertext)
    pad_len = plaintext[-1]
    return plaintext[:-pad_len]

def compute_crc32(data: bytes) -> bytes:
    return struct.pack('>I', binascii.crc32(data) & 0xFFFFFFFF)

def icmp_checksum(data: bytes) -> int:
    s = 0
    for i in range(0, len(data), 2):
        w = (data[i] << 8) + (data[i+1] if i+1 < len(data) else 0)
        s += w
    while s >> 16:
        s = (s & 0xFFFF) + (s >> 16)
    return ~s & 0xFFFF

def build_icmp(payload: bytes, seq: int = 1) -> bytes:
    hdr = struct.pack('>BBHHH', 8, 0, 0, 0x1234, seq)
    chk = icmp_checksum(hdr + payload)
    return struct.pack('>BBHHH', 8, 0, chk, 0x1234, seq) + payload

def build_ip(total_length: int, src: str, dst: str) -> bytes:
    src_b = bytes(int(x) for x in src.split('.'))
    dst_b = bytes(int(x) for x in dst.split('.'))
    return struct.pack('>BBHHHBBH4s4s',
        0x45, 0, total_length, 0xABCD, 0, 128, 1, 0, src_b, dst_b)

def build_ping_packet(icmp_payload: bytes, src: str, dst: str, seq: int = 1) -> bytes:
    icmp_payload = icmp_payload[:32].ljust(32, b'\x00')  # pad to 32 bytes (Windows)
    icmp = build_icmp(icmp_payload, seq)
    ip   = build_ip(20 + len(icmp), src, dst)
    return ip + icmp  # 60 bytes

def build_dump(name, surname, id_, gender, icmp_payload, src_ip, dst_ip):
    nb = name.encode()
    sb = surname.encode()
    ib = id_.encode()

    key    = derive_key(nb, sb, ib, gender)
    packet = build_ping_packet(icmp_payload, src_ip, dst_ip)  # 60 bytes
    enc    = encrypt_ecb(key, packet)                          # 64 bytes

    plain = (
        pad_field(nb, 25) +
        pad_field(sb, 25) +
        pad_field(ib, 16) +
        bytes([gender]) +
        enc
    )  # 131 bytes

    return plain + compute_crc32(plain)  # 135 bytes

def corrupt_byte(data: bytes, offset: int, new_value: int) -> bytes:
    d = bytearray(data)
    d[offset] = new_value
    return bytes(d)

def print_dump(label, data):
    print(f"\n{'─'*52}")
    print(f"  {label}  ({len(data)} bytes)")
    print(f"{'─'*52}")
    print(data.hex())
    print(f"\n  Name     (0 -24) : {data[0:25].rstrip(b'\\x00')}")
    print(f"  Surname  (25-49) : {data[25:50].rstrip(b'\\x00')}")
    print(f"  ID       (50-65) : {data[50:66].rstrip(b'\\x00')}")
    print(f"  Gender   (66)    : {data[66]} ({'M' if data[66]==1 else 'F' if data[66]==2 else '?'})")
    print(f"  Enc pkt  (67-130): {data[67:131].hex()}")
    print(f"  CRC32    (131-134): {data[131:135].hex()}")

# ─────────────────────────────────────────
#  DUMP 1 — valid, contains FLAG part 1
# ─────────────────────────────────────────

dump1 = build_dump(
    name         = "Rexxy",
    surname      = "Wonderland",
    id_          = "ID-2026-CTF-0001",
    gender       = 0x01,
    icmp_payload = b"CyberSci{1nT3lh3X}",
    src_ip       = "0.168.1.10",
    dst_ip       = "0.168.1.1"
)

# ─────────────────────────────────────────
#  DUMP 2 — corrupted personal data
#  Byte 3 of Name flipped: 'i' → 0xFF
#  CRC left INVALID so players detect it
# ─────────────────────────────────────────

dump2_clean = build_dump(
    name         = "Felix",
    surname      = "Worldending",
    id_          = "ID-2026-CTF-0002",
    gender       = 0x02,
    icmp_payload = b"CyberSci{so_m4ny_p",
    src_ip       = "0.168.1.11",
    dst_ip       = "0.168.1.1"
)
dump2 = corrupt_byte(dump2_clean, 3, 0x23)

# ─────────────────────────────────────────
#  DUMP 3 — corrupted ICMP type byte
#  CRC is recomputed → VALID (sneaky)
#  Corruption is hidden inside encryption
# ─────────────────────────────────────────

dump3_clean = build_dump(
    name         = "Aristotle",
    surname      = "Wideeyed",
    id_          = "ID-2026-CTF-0003",
    gender       = 0x01,
    icmp_payload = b"igeons_63accd2_90}",
    src_ip       = "0.0.0.5",
    dst_ip       = "0.0.0.1"
)

key3     = derive_key(b"Aristotle", b"Wideeyed", b"ID-2026-CTF-0003", 0x01)
dec3     = bytearray(decrypt_ecb(key3, dump3_clean[67:131]))
dec3[20] = 0x00  # corrupt ICMP type: 8 (Echo Request) → 0 (Echo Reply)
re_enc3  = encrypt_ecb(key3, bytes(dec3))

plain3 = dump3_clean[:67] + re_enc3
dump3  = plain3 + compute_crc32(plain3)  # CRC valid, corruption hidden

# ─────────────────────────────────────────
#  OUTPUT
# ─────────────────────────────────────────

print_dump("DUMP 1 — Valid", dump1)
print_dump("DUMP 2 — Corrupted name byte (CRC invalid)", dump2)
print_dump("DUMP 3 — Corrupted ICMP type (CRC valid, sneaky)", dump3)

for label, dump in [("dump1", dump1), ("dump2", dump2), ("dump3", dump3)]:
    with open(f"{label}.hex", "w") as f:
        f.write(dump.hex())
    print(f"\nSaved {label}.hex  ({len(dump)} bytes)")