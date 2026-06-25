"""
server.py - CySpace.com Private Messaging API

Listens on 0.0.0.0:1337. Presents a Telnet-era banner, reads a canonical
signing envelope and DSA (r, s) signature from the client, verifies the
signature under @viper92's public key y, and returns the flag on success.

DSA parameters and flag are loaded from secret.txt at startup.

Protocol (per cyspace_api.txt):
  Server sends: banner + "> " prompt
  Client sends: envelope line (e.g. "INBOX-deadbeef|1751673600|@viper92|INBOX_REQUEST")
  Client sends: "r=<integer>"
  Client sends: "s=<integer>"
  Server sends: inbox contents (flag) or "SIGNATURE VERIFICATION FAILED"

Usage:
    python server.py
"""

import hashlib
import os
import socketserver
import sys

SECRET_PATH = os.path.join(os.path.dirname(__file__), "secret.txt")
HOST        = "0.0.0.0"
PORT        = 1337

# ---------------------------------------------------------------------------
# Load parameters from secret.txt
# ---------------------------------------------------------------------------

def load_secret():
    cfg = {}
    with open(SECRET_PATH) as f:
        for line in f:
            line = line.strip()
            if "=" in line:
                k, v = line.split("=", 1)
                cfg[k.strip()] = v.strip()
    return (
        int(cfg["p"]), int(cfg["q"]), int(cfg["g"]),
        int(cfg["y"]), cfg["FLAG"],
    )

try:
    P, Q, G, Y, FLAG = load_secret()
except FileNotFoundError:
    print(f"ERROR: {SECRET_PATH} not found. Run generate_posts.py first.", file=sys.stderr)
    sys.exit(1)

# ---------------------------------------------------------------------------
# DSA verification
# ---------------------------------------------------------------------------

def sha1_int(data: bytes) -> int:
    return int(hashlib.sha1(data).hexdigest(), 16)

def dsa_verify(envelope_bytes: bytes, r: int, s: int) -> bool:
    if not (0 < r < Q and 0 < s < Q):
        return False
    h  = sha1_int(envelope_bytes)
    w  = pow(s, -1, Q)
    u1 = h * w % Q
    u2 = r * w % Q
    v  = (pow(G, u1, P) * pow(Y, u2, P) % P) % Q
    return v == r

# ---------------------------------------------------------------------------
# Protocol
# ---------------------------------------------------------------------------

BANNER = (
    b"\r\n"
    b"============================================================\r\n"
    b" CySpace.com  --  Private Messaging API  v0.9 (beta)\r\n"
    b" DSA/SHA-1 authentication  |  FIPS 186-1 (1994)\r\n"
    b" Running on salvaged Pentium II  --  post-EMP rebuild\r\n"
    b" See cyspace_api.txt for request format.\r\n"
    b"============================================================\r\n"
    b"\r\n"
    b"> "
)

INBOX_CONTENTS = (
    "============================================================\r\n"
    " @viper92 -- PRIVATE INBOX\r\n"
    "============================================================\r\n"
    "\r\n"
    "FROM: handler@remnant.net\r\n"
    "SUBJ: re: package\r\n"
    "\r\n"
    "good work. the key worked. next drop is at the usual relay.\r\n"
    "use the new passphrase:\r\n"
    "\r\n"
    "{FLAG}\r\n"
    "\r\n"
    "destroy after reading.\r\n"
    "============================================================\r\n"
)

class CySpaceHandler(socketserver.StreamRequestHandler):
    def handle(self):
        self.request.settimeout(10)
        try:
            self.wfile.write(BANNER)
            self.wfile.flush()

            envelope_line = self.rfile.readline(1024).decode(errors="replace").strip()
            r_line        = self.rfile.readline(256).decode(errors="replace").strip()
            s_line        = self.rfile.readline(256).decode(errors="replace").strip()

            if not (r_line.startswith("r=") and s_line.startswith("s=")):
                self.wfile.write(b"PROTOCOL ERROR: expected r=<int> then s=<int>\r\n")
                self.wfile.flush()
                return

            r = int(r_line[2:])
            s = int(s_line[2:])

            if dsa_verify(envelope_line.encode("utf-8"), r, s):
                response = INBOX_CONTENTS.replace("{FLAG}", FLAG)
                self.wfile.write(response.encode())
            else:
                self.wfile.write(b"SIGNATURE VERIFICATION FAILED\r\n")

            self.wfile.flush()
        except (ValueError, ConnectionResetError, BrokenPipeError, TimeoutError):
            pass

class ThreadedTCPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    allow_reuse_address = True
    daemon_threads      = True

if __name__ == "__main__":
    print(f"CySpace.com API listening on {HOST}:{PORT}")
    with ThreadedTCPServer((HOST, PORT), CySpaceHandler) as server:
        server.serve_forever()
