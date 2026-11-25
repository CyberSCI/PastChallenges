#!/usr/bin/env python3

# CyberSci Regionals 2026/27
#
# Beaver Tail solve script by Dmitriy Beryoza (0xd13a@gmail.com)

import gzip
import urllib.request
import hashlib
import io
import struct
import filecmp
from scapy.all import IP, TCP, PcapNgReader
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

# Decode Flag 1

request = urllib.request.Request("https://weakpass.com/download/90/rockyou.txt.gz", headers={"User-Agent": "Mozilla/5.0"})

with urllib.request.urlopen(request, timeout=60) as response:

    with gzip.GzipFile(fileobj=response) as gz:
        while True:
            line = gz.readline()
            if not line:  # End of file
                break

            line = line.decode("utf-8", errors="replace").rstrip("\r\n")

            if hashlib.blake2b(line.encode()).hexdigest() == "a744822aafb8113d64c4010323eb5f9306a88b3fd5ecc2f7501759cb721074dc22feb664f72b46de745281a35625c2cd2ddab784af11c55a065796dadb9351fe":
               print(f"Flag 1: {line}\n")
               break

# Decode flag 2

def untwister(text: str) -> str:
    mask = [
        112, 100, 202, 142, 35, 126, 58, 252, 67, 52, 13, 155,
        100, 185, 89, 38, 35, 174, 2, 93, 51, 195, 137, 196,
        221, 251, 199, 0, 124, 204, 98, 248, 231, 146, 218, 107,
        167, 241, 90, 193, 111, 82, 186, 145, 66, 241, 249, 150,
        73, 111, 242, 196, 89, 52
    ]

    if len(text) != len(mask) or any(ord(c) > 255 for c in text):
        raise ValueError(f"Expected exactly {len(mask)} byte characters")

    def rotate_bits_right(value: int, count: int) -> int:
        return ((value >> count) | (value << (8 - count))) & 0xFF

    # Undo the final XOR.
    values = [ord(char) ^ key for char, key in zip(text, mask)]

    for round_num in range(99, -1, -1):
        # Undo the reversal.
        if round_num % 2 == 0:
            values.reverse()

        # Undo the array rotation by rotating right.
        offset = (7 * round_num + 11) % len(values)
        if offset:
            values = values[-offset:] + values[:-offset]

        # Undo the bit rotation, then the byte shift.
        values = [
            (
                rotate_bits_right(byte, (index + round_num) % 7 + 1)
                - 17 * index
                - 29 * round_num
                - 43
            ) & 0xFF
            for index, byte in enumerate(values)
        ]

    return "".join(chr(value) for value in values)


print("Flag 2: " + untwister("CyberSci{AI_and_living_things_will_peacefully_coexist}") + "\n")


# Decode flag 3

def open_tcp_stream(pcap_path, src_ip, src_port, dst_ip, dst_port):
    segments = []

    with PcapNgReader(pcap_path) as capture:
        for packet in capture:

            if IP not in packet or TCP not in packet:
                continue

            ip = packet[IP]
            tcp = packet[TCP]

            if (ip.src, tcp.sport, ip.dst, tcp.dport) != (
                src_ip, src_port, dst_ip, dst_port
            ):
                continue

            payload = bytes(tcp.payload)
            if payload:
                # SYN consumes one sequence number.
                sequence = int(tcp.seq) + int(bool(tcp.flags.S))
                segments.append((sequence, payload))

    if not segments:
        raise ValueError("No TCP payload found for this direction")

    segments.sort(key=lambda segment: segment[0])

    data = bytearray()
    expected = segments[0][0]

    for sequence, payload in segments:
        if sequence > expected:
            raise ValueError(
                f"Missing {sequence - expected} bytes in the capture"
            )

        # Skip bytes already collected, including retransmissions.
        overlap = expected - sequence
        if overlap < len(payload):
            data.extend(payload[overlap:])
            expected = sequence + len(payload)

    return io.BytesIO(data)

def decrypt(key, record, context):
    return AESGCM(key).decrypt(record[:12], record[12:], context)


print("Decoding file for Flag 3")

stream = open_tcp_stream(
    "../release_files/traffic.pcapng",
    src_ip="10.0.2.20",
    src_port=40548,
    dst_ip="10.10.10.3",
    dst_port=0xA1A1,
)

while True:
    type = ord(stream.read(1))
    
    if type == 1:
        length = ord(stream.read(1))
        pwd = stream.read(length)
        print("Password: ", pwd)
        key = stream.read(32)
    
    if type == 2:
        length = ord(stream.read(1))
        encrypted = stream.read(12 + length + 16)
        filename = decrypt(key, encrypted, b"filename").decode()
        print(f"Requested file: {filename}")

    if type == 0:
        break

stream = open_tcp_stream(
    "../release_files/traffic.pcapng",
    src_ip="10.10.10.3",
    src_port=0xA1A1,
    dst_ip="10.0.2.20",
    dst_port=40548,
)

type = ord(stream.read(1))
    
type = ord(stream.read(1))

size, = struct.unpack(">I", decrypt(key, stream.read(12 + 4 + 16), b"file-length"))
data = decrypt(key, stream.read(12 + size + 16), b"file-data")

with open(filename, "wb") as file:
    file.write(data)

print("Files match: " + str(filecmp.cmp(filename, "../server_files/den-blueprint.png", shallow=False)))
