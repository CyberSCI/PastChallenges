#!/usr/bin/env python3

# CyberSci Regionals 2026/27
#
# Beaver Tail test client by Dmitriy Beryoza (0xd13a@gmail.com)

import argparse
import getpass
import os
from pathlib import Path
import socket
import struct

from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

PORT = 0xA1A1
MAX_FILE = 16 * 1024 * 1024


def recv_exact(sock, count):
    parts = bytearray()
    while len(parts) < count:
        chunk = sock.recv(count - len(parts))
        if not chunk:
            raise ConnectionError("Server closed the connection")
        parts.extend(chunk)
    return bytes(parts)


def encrypt(key, plaintext, context):
    nonce = os.urandom(12)
    return nonce + AESGCM(key).encrypt(nonce, plaintext, context)


def decrypt(key, record, context):
    return AESGCM(key).decrypt(record[:12], record[12:], context)


def encoded_field(text, label):
    data = text.encode("utf-8")
    if not 1 <= len(data) <= 255:
        raise ValueError(f"{label} must contain 1 to 255 UTF-8 bytes")
    return data


class Client:
    def __init__(self, host="127.0.0.1"):
        self.sock = socket.create_connection((host, PORT), timeout=30)
        self.key = None

    def _status(self):
        status = recv_exact(self.sock, 1)[0]
        if status not in (0, 1):
            raise ConnectionError("Invalid response type")
        return status == 1

    def login(self, password):
        data = encoded_field(password, "Password")
        self.key = None
        key = os.urandom(32)
        self.sock.sendall(bytes([1, len(data)]) + data + key)
        if self._status():
            self.key = key
            return True
        return False

    def download(self, filename):
        if self.key is None:
            raise ValueError("Log in first")
        name = encoded_field(filename, "Filename")
        self.sock.sendall(bytes([2, len(name)]) + encrypt(self.key, name, b"filename"))
        if not self._status():
            return None
        length_record = recv_exact(self.sock, 12 + 4 + 16)
        size, = struct.unpack(">I", decrypt(self.key, length_record, b"file-length"))
        if size > MAX_FILE:
            raise ConnectionError("File exceeds the 16 MiB limit")
        return decrypt(self.key, recv_exact(self.sock, 12 + size + 16), b"file-data")

    def disconnect(self):
        try:
            self.sock.sendall(b"\x00")
            return self._status()
        finally:
            self.close()

    def close(self):
        self.key = None
        self.sock.close()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", default="127.0.0.1")
    args = parser.parse_args()
    try:
        client = Client(args.host)
    except OSError as error:
        print(f"Connection failed: {error}")
        return 1
    print(f"Connected to {args.host}:{PORT}")
    try:
        while True:
            print("\n1. Login\n2. Download file\n0. Disconnect")
            choice = input("> ").strip()
            try:
                if choice == "1":
                    print("Login successful" if client.login(getpass.getpass("Password: "))
                          else "Login failed")
                elif choice == "2":
                    if client.key is None:
                        print("Log in first")
                        continue
                    name = input("Remote filename: ").strip()
                    # Ask for the local destination before sending the request.
                    default = Path(name).name or "download.bin"
                    destination = Path(input(f"Save as [{default}]: ").strip() or default)
                    data = client.download(name)
                    if data is None:
                        print("Download failed (unavailable file or invalid request)")
                        continue
                    try:
                        # Avoid overwriting an existing local file.
                        with destination.open("xb") as output:
                            output.write(data)
                        print(f"Saved {len(data)} bytes to {destination}")
                    except OSError as error:
                        print(f"Could not save file: {error}")
                elif choice == "0":
                    print("Disconnected" if client.disconnect() else "Disconnect rejected")
                    break
                else:
                    print("Choose 0, 1, or 2")
            except ValueError as error:
                print(error)
    except (OSError, ConnectionError, InvalidTag) as error:
        print(f"Connection or encryption error: {error or 'authentication failed'}")
        return 1
    except (KeyboardInterrupt, EOFError):
        print("\nClosing connection")
    finally:
        client.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
