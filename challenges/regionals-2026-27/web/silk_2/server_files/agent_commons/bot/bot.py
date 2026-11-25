import logging
import os
import re
import time
from urllib.parse import urlsplit

import requests


logging.basicConfig(level=os.environ.get("LOG_LEVEL", "INFO"))
LOGGER = logging.getLogger("agent_commons.bot")


def compile_patterns(raw_patterns):
    patterns = [item.strip() for item in raw_patterns.split(",") if item.strip()]
    try:
        return [re.compile(item, re.IGNORECASE) for item in patterns]
    except re.error as exc:
        raise ValueError(f"BOT_FLAGGED_PATTERNS contains an invalid regular expression: {exc}") from exc


def validated_api_origin(raw_url):
    parsed = urlsplit(raw_url)
    if (
        parsed.scheme != "http"
        or parsed.hostname != "web"
        or parsed.port != 8000
        or parsed.username is not None
        or parsed.password is not None
        or parsed.path not in ("", "/")
        or parsed.query
        or parsed.fragment
    ):
        raise ValueError("API_BASE_URL must be the internal origin http://web:8000.")
    return "http://web:8000"


def parse_pending_reports(markdown):
    reports = []
    current = None
    for line in markdown.splitlines():
        report_match = re.match(r"^## Report (\d+) \| pending$", line)
        if report_match:
            if current and "url" in current:
                reports.append(current)
            current = {"id": int(report_match.group(1))}
            continue
        if current:
            url_match = re.match(r"^URL: (\S+)$", line)
            if url_match:
                current["url"] = url_match.group(1)
    if current and "url" in current:
        reports.append(current)
    return reports


class ReportBot:
    def __init__(self, api_origin, username, password, patterns, timeout=5):
        self.api_origin = validated_api_origin(api_origin)
        self.username = username
        self.password = password
        self.patterns = patterns
        self.timeout = timeout
        self.session = requests.Session()
        self.session.trust_env = False
        self.token = None
        self.token_expires_at = 0

    def request(self, method, path, *, json=None):
        if not path.startswith("/") or path.startswith("//"):
            raise ValueError("API path must be an absolute local path.")
        response = self.session.request(
            method,
            self.api_origin + path,
            headers={"X-API-Token": self.token} if self.token else {},
            json=json,
            timeout=self.timeout
        )
        response.raise_for_status()
        return response

    def login(self):
        response = self.session.post(
            self.api_origin + "/login/",
            json={"username": self.username, "password": self.password},
            timeout=self.timeout
        )
        response.raise_for_status()
        payload = response.json()
        if payload.get("token_type") != "API-Token" or not payload.get("access_token"):
            raise RuntimeError("The internal login endpoint returned an invalid token response.")
        self.token = payload["access_token"]
        lifetime = int(payload.get("expires_in", 3600))
        self.token_expires_at = time.monotonic() + max(1, lifetime - 60)

    def ensure_login(self):
        if not self.token or time.monotonic() >= self.token_expires_at:
            self.login()

    def process_report(self, report):
        report_id = int(report["id"])
        matched = False
        try:
            url = report["url"]
            post_response = self.request("GET", url)
            content = post_response.text
            matched = any(pattern.search(content) for pattern in self.patterns)
            post_match = re.fullmatch(r"/posts/(\d+)/content/", urlsplit(url).path)
            if matched and post_match:
                self.request(
                    "POST",
                    f"/posts/{post_match.group(1)}/visibility/",
                    json={"visibility": "admin"},
                )
        finally:
            self.request("POST", f"/admin/reports/{report_id}/resolve/")
        LOGGER.info("Resolved report %s; flagged=%s", report_id, matched)

    def poll_once(self):
        self.ensure_login()
        response = self.request("GET", "/admin/reports/?status=pending")
        reports = parse_pending_reports(response.text)
        for report in reports:
            try:
                self.process_report(report)
            except Exception as exc:
                LOGGER.warning(
                    "Report %s encountered an error while processing or resolving: %s",
                    report.get("id", "unknown"),
                    exc,
                )

    def run_forever(self, interval):
        while True:
            started = time.monotonic()
            try:
                self.poll_once()
            except (requests.RequestException, RuntimeError, ValueError) as exc:
                LOGGER.warning("Report polling failed: %s", exc)
                self.token = None
            elapsed = time.monotonic() - started
            time.sleep(max(0, interval - elapsed))


def main():
    raw_interval = int(os.environ.get("BOT_POLL_INTERVAL", "10"))
    timeout = int(os.environ.get("BOT_REQUEST_TIMEOUT", "5"))
    if raw_interval < 1 or timeout < 1:
        raise ValueError("Polling interval and request timeout must be positive integers.")
    patterns = compile_patterns(os.environ.get("BOT_FLAGGED_PATTERNS", "bad bot"))
    bot = ReportBot(
        api_origin=os.environ.get("API_BASE_URL", "http://web:8000"),
        username=os.environ["BOT_USERNAME"],
        password=os.environ["BOT_PASSWORD"],
        patterns=patterns,
        timeout=timeout,
    )
    bot.run_forever(raw_interval)


if __name__ == "__main__":
    main()