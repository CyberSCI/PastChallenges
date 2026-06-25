"""
server.py - CyberKinz.com Member Services Terminal

Listens on 0.0.0.0:1337. Presents a BBS-style banner, prompts for username
and password, returns the flag for valid credentials.

Credentials and flag are loaded from secret.txt at startup.
No oracle: identical error message for wrong username or wrong password.

Usage:
    python server.py
"""

import hmac
import socketserver
import os
import sys

SECRET_PATH = os.path.join(os.path.dirname(__file__), "secret.txt")
HOST        = "0.0.0.0"
PORT        = 1337

# ---------------------------------------------------------------------------
# Load credentials from secret.txt
# ---------------------------------------------------------------------------

def load_secret():
    cfg = {}
    with open(SECRET_PATH) as f:
        for line in f:
            line = line.strip()
            if "=" in line:
                k, v = line.split("=", 1)
                cfg[k.strip()] = v.strip()
    return cfg["VALID_USER"], cfg["VALID_PASS"], cfg["FLAG"]

try:
    VALID_USER, VALID_PASS, FLAG = load_secret()
except FileNotFoundError:
    print(f"ERROR: {SECRET_PATH} not found. Run generate_keys.py first.", file=sys.stderr)
    sys.exit(1)

# ---------------------------------------------------------------------------
# Protocol
# ---------------------------------------------------------------------------

BANNER = (
    b"\r\n"
    b"============================================================\r\n"
    b" CYBERKINZ.COM  --  Member Services Terminal  v1.2\r\n"
    b" Running CyberOS/286  (c) 1997 CyberKinz Corp.\r\n"
    b" Dial-up access restored post-EMP. Welcome back.\r\n"
    b"============================================================\r\n"
    b"\r\n"
    b"Username: "
)

PASS_PROMPT  = b"Password: "
LOGIN_OK     = b"LOGIN OK\r\n"
LOGIN_FAIL   = b"LOGIN FAILED\r\nInvalid credentials.\r\n"

class CyberKinzHandler(socketserver.StreamRequestHandler):
    def handle(self):
        self.request.settimeout(10)
        try:
            self.wfile.write(BANNER)
            self.wfile.flush()

            username = self.rfile.readline(1024).decode(errors="replace").strip()

            self.wfile.write(PASS_PROMPT)
            self.wfile.flush()

            password = self.rfile.readline(1024).decode(errors="replace").strip()

            user_ok = hmac.compare_digest(username, VALID_USER)
            pass_ok = hmac.compare_digest(password, VALID_PASS)
            if user_ok and pass_ok:
                self.wfile.write(LOGIN_OK)
                self.wfile.write(f"Welcome, {username}!\r\n".encode())
                self.wfile.write(f"{FLAG}\r\n".encode())
            else:
                self.wfile.write(LOGIN_FAIL)
            self.wfile.flush()
        except (ConnectionResetError, BrokenPipeError):
            pass

class ThreadedTCPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    allow_reuse_address = True
    daemon_threads      = True

if __name__ == "__main__":
    with ThreadedTCPServer((HOST, PORT), CyberKinzHandler) as server:
        print(f"CyberKinz.com listening on {HOST}:{PORT}")
        server.serve_forever()
