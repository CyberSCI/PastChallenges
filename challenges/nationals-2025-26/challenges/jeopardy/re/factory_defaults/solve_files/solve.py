#!/usr/bin/env python3
"""
Solve script for factory_defaults.

Intended path:
  1. Reverse the server binary to understand the IPBX-AMI binary protocol.
  2. The password is not stored in plaintext — find it in dashboard.html > Setup Guide.
  3. Authenticate, then send CONT_CHAN_LIST to list active channels.
  4. Spot the suspicious 'SIP/flag-00000000' channel in the response.
  5. Send CONT_CHAN_DETAIL with that channel name to retrieve the flag.

Usage: python3 solve.py [host] [port]
"""

import base64
import socket
import struct
import sys
import time

HOST = sys.argv[1] if len(sys.argv) > 1 else '127.0.0.1'
PORT = int(sys.argv[2]) if len(sys.argv) > 2 else 5038

# ── Protocol constants ────────────────────────────────────────────────────────

MAGIC = 0xa1307f49

# MsgType
AUTH   = 0x02
STATUS = 0x04

# ContType
CONT_REQUEST    = 0x20
CONT_RESPONSE   = 0x21
CONT_CHAN_LIST   = 0x31
CONT_CHAN_DETAIL = 0x34
CONT_ERROR      = 0xFF

# Struct layouts (little-endian, packed)
HDR_FMT       = '<IIIIIIIIII'   # 10 x uint32 = 40 bytes
HDR_SIZE      = struct.calcsize(HDR_FMT)
BODY_HDR_FMT  = '<II'           # ptype + length = 8 bytes
BODY_HDR_SIZE = struct.calcsize(BODY_HDR_FMT)

# ── Hash ──────────────────────────────────────────────────────────────────────
#
#  XOR of every CtlHdr field except msg_hash, then XOR each body byte
#  shifted into a 32-bit accumulator by (i % 4) * 8 bits.

def compute_hash(magic, mtype, src, dest, stype, flags,
                 msg_len, timestamp, client_id, body: bytes) -> int:
    h = 0
    for v in (magic, mtype, src, dest, stype, flags, msg_len, timestamp, client_id):
        h ^= v
    for i, b in enumerate(body):
        h ^= b << ((i % 4) * 8)
    return h & 0xFFFFFFFF

# ── Packet helpers ────────────────────────────────────────────────────────────

def build_packet(mtype: int, ptype: int, value: bytes = b'') -> bytes:
    body    = struct.pack(BODY_HDR_FMT, ptype, len(value)) + value
    msg_len = len(body)
    ts      = int(time.time())
    src = client_id = 1
    h   = compute_hash(MAGIC, mtype, src, 0, 0, 0, msg_len, ts, client_id, body)
    hdr = struct.pack(HDR_FMT, MAGIC, mtype, src, 0, 0, 0, msg_len, h, ts, client_id)
    return hdr + body


def recv_exact(sock: socket.socket, n: int) -> bytes:
    buf = b''
    while len(buf) < n:
        chunk = sock.recv(n - len(buf))
        if not chunk:
            raise EOFError('connection closed')
        buf += chunk
    return buf


def recv_packet(sock: socket.socket) -> tuple:
    """Return (mtype, ptype, value_bytes)."""
    hdr_raw = recv_exact(sock, HDR_SIZE)
    fields  = struct.unpack(HDR_FMT, hdr_raw)
    # fields: magic mtype src dest stype flags msg_len msg_hash timestamp client_id
    msg_len = fields[6]
    body    = recv_exact(sock, msg_len)

    ptype, length = struct.unpack(BODY_HDR_FMT, body[:BODY_HDR_SIZE])
    value         = body[BODY_HDR_SIZE: BODY_HDR_SIZE + length]
    return fields[1], ptype, value   # mtype, ptype, value

# ── Session helper ────────────────────────────────────────────────────────────

def connect_and_auth() -> socket.socket:
    """Open a new connection and complete the AUTH handshake."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((HOST, PORT))
    sock.recv(64)   # discard "IPBX-AMI/1.0\r\n" banner

    # Credentials found in dashboard.html > Setup Guide (Step 3)
    creds = base64.b64encode(b'admin:s3cr3t_pbx')
    sock.sendall(build_packet(AUTH, CONT_REQUEST, creds))

    _, ptype, value = recv_packet(sock)
    if ptype == CONT_ERROR:
        raise RuntimeError(f'auth failed: {value.decode()}')
    return sock

# ── Solve ─────────────────────────────────────────────────────────────────────

def solve():
    print(f'[*] target  {HOST}:{PORT}')

    # Step 1 — list active channels
    sock = connect_and_auth()
    print('[+] authenticated')

    sock.sendall(build_packet(STATUS, CONT_CHAN_LIST))
    _, ptype, value = recv_packet(sock)
    sock.close()

    if ptype == CONT_ERROR:
        raise RuntimeError(f'CHAN_LIST error: {value.decode()}')

    raw = value.decode()
    print(f'[*] channel list: {raw}')

    # Parse semicolon-delimited entries, each with comma-delimited key=value pairs
    flag_chan = None
    for entry in raw.split(';'):
        fields = dict(kv.split('=', 1) for kv in entry.split(',') if '=' in kv)
        if 'flag' in fields.get('channel', ''):
            flag_chan = fields['channel']
            break

    if not flag_chan:
        raise RuntimeError('flag channel not found in channel list')
    print(f'[+] flag channel: {flag_chan}')

    # Step 2 — retrieve channel detail
    # (server closes the connection after each post-auth command; reconnect)
    sock = connect_and_auth()
    sock.sendall(build_packet(STATUS, CONT_CHAN_DETAIL, flag_chan.encode()))
    _, ptype, value = recv_packet(sock)
    sock.close()

    if ptype == CONT_ERROR:
        raise RuntimeError(f'CHAN_DETAIL error: {value.decode()}')

    detail = value.decode()
    print(f'[*] channel detail: {detail}')

    fields = dict(kv.split('=', 1) for kv in detail.split(',') if '=' in kv)
    flag   = fields.get('info', '')
    if not flag:
        raise RuntimeError('flag not found in channel detail response')

    print(f'\n[+] {flag}')


if __name__ == '__main__':
    solve()
