from dataclasses import replace

import pytest
from fastapi.testclient import TestClient
from starlette.websockets import WebSocketDisconnect

from server_files.app import create_app


def connect(client, headers=None):
    # TestClient uses ws://testserver internally, so it omits HTTPS-only cookies.
    # Supply the cookie a browser sends over wss:// for this test origin.
    request_headers = dict(headers or {})
    if session_id := client.cookies.get("damwatch_session"):
        request_headers["cookie"] = f"damwatch_session={session_id}"
    return client.websocket_connect("/ws/telemetry", headers=request_headers)


def test_public_topic_catalog_and_snapshot_contain_no_flag(settings):
    with TestClient(create_app(settings), base_url=settings.public_origin) as client:
        client.get("/")
        catalog = client.get("/api/topics")
        with connect(client, headers={"origin": settings.public_origin}) as socket:
            socket.send_json({"action": "subscribe", "topic": "water/level"})
            snapshot = socket.receive_json()

    assert catalog.status_code == 200
    assert catalog.json()["topics"] == [
        {"name": "water/level", "access": "public"},
        {"name": "operations/triage", "access": "restricted"},
    ]
    assert snapshot["topic"] == "water/level"
    assert snapshot["public_status"] == "NORMAL"
    assert snapshot["baseline_cm"] - snapshot["waterline_cm"] == 41
    assert all(
        flag not in str((catalog.json(), snapshot))
        for flag in ("test-one", "test-two", "test-three")
    )


def test_restricted_subscribe_replays_only_first_flag(settings):
    with TestClient(create_app(settings), base_url=settings.public_origin) as client:
        client.get("/")
        with connect(client, headers={"origin": settings.public_origin}) as socket:
            socket.send_json({"action": "subscribe", "topic": "operations/triage"})
            incident = socket.receive_json()

    assert incident["id"] == "INC-017"
    assert incident["memo"] == "coolant-diversion.memo"
    assert "Unexpected drawdown" in incident["message"]
    assert "Inspector's record: coolant-diversion.memo" in incident["message"]
    assert incident["flag"] == settings.flag_1
    assert settings.flag_2 not in str(incident)
    assert settings.flag_3 not in str(incident)


def test_websocket_rejects_missing_session_and_foreign_browser_origin(settings):
    with TestClient(create_app(settings), base_url=settings.public_origin) as client:
        with pytest.raises(WebSocketDisconnect) as missing, connect(client):
            pass
        client.get("/")
        with (
            pytest.raises(WebSocketDisconnect) as foreign,
            connect(client, headers={"origin": "https://attacker.test"}),
        ):
            pass

    assert missing.value.code == 1008
    assert foreign.value.code == 1008


def test_cli_without_origin_can_subscribe(settings):
    with TestClient(create_app(settings), base_url=settings.public_origin) as client:
        client.get("/")
        with connect(client) as socket:
            socket.send_json({"action": "subscribe", "topic": "water/level"})
            assert socket.receive_json()["topic"] == "water/level"


def test_unknown_messages_do_not_reveal_incident(settings):
    with TestClient(create_app(settings), base_url=settings.public_origin) as client:
        client.get("/")
        with connect(client) as socket:
            socket.send_json({"action": "read", "topic": "operations/triage"})
            first = socket.receive_json()
            socket.send_json({"action": "subscribe", "topic": "operations/private"})
            second = socket.receive_json()

    assert first["error"] == "unknown_action"
    assert second["error"] == "unknown_topic"
    assert all(settings.flag_1 not in str(frame) for frame in (first, second))


def test_malformed_and_oversized_messages_close_socket(settings):
    with TestClient(create_app(settings), base_url=settings.public_origin) as client:
        client.get("/")
        with pytest.raises(WebSocketDisconnect) as malformed, connect(client) as socket:
            socket.send_text("{")
            socket.receive_json()
        with pytest.raises(WebSocketDisconnect) as oversized, connect(client) as socket:
            socket.send_text("x" * 4097)
            socket.receive_json()

    assert malformed.value.code == 1003
    assert oversized.value.code == 1009


def test_socket_limit_releases_capacity_after_close(settings):
    limited = replace(settings, max_ws_per_session=1, max_ws_total=1)
    with TestClient(create_app(limited), base_url=limited.public_origin) as client:
        client.get("/")
        with (
            connect(client),
            pytest.raises(WebSocketDisconnect) as full,
            connect(client),
        ):
            pass
        with connect(client) as socket:
            socket.send_json({"action": "subscribe", "topic": "water/level"})
            assert socket.receive_json()["topic"] == "water/level"

    assert full.value.code == 1013


def test_idle_socket_closes_without_http_session_touch(settings):
    limited = replace(settings, ws_idle_seconds=0.01)
    with TestClient(create_app(limited), base_url=limited.public_origin) as client:
        client.get("/")
        with pytest.raises(WebSocketDisconnect) as idle, connect(client) as socket:
            socket.receive_json()

    assert idle.value.code == 1000
