from dataclasses import replace

import pytest
from fastapi.testclient import TestClient

from server_files.app import create_app
from server_files.state import SessionCapacityError, SessionStore


class Clock:
    def __init__(self, value: float = 0.0):
        self.value = value

    def __call__(self) -> float:
        return self.value


def test_page_issues_secure_opaque_cookie_and_reuses_it(settings):
    with TestClient(
        create_app(settings, clock=Clock()), base_url=settings.public_origin
    ) as first:
        response = first.get("/")
        cookie = first.cookies.get("damwatch_session")
        again = first.get("/")

    with TestClient(
        create_app(settings, clock=Clock()), base_url=settings.public_origin
    ) as second:
        second.get("/")
        other_cookie = second.cookies.get("damwatch_session")

    assert response.status_code == 200
    assert cookie and len(cookie) >= 32
    assert cookie != other_cookie
    assert first.cookies.get("damwatch_session") == cookie
    assert again.status_code == 200
    assert "httponly" in response.headers["set-cookie"].lower()
    assert "secure" in response.headers["set-cookie"].lower()
    assert "samesite=lax" in response.headers["set-cookie"].lower()


def test_http_activity_extends_session_but_health_does_not(settings):
    clock = Clock()
    ttl = settings.session_ttl_seconds
    with TestClient(
        create_app(settings, clock=clock), base_url=settings.public_origin
    ) as client:
        client.get("/")
        original = client.cookies.get("damwatch_session")
        clock.value = ttl - 1
        client.get("/")
        assert client.cookies.get("damwatch_session") == original

        clock.value = 2 * ttl - 2
        client.get("/healthz")
        clock.value = 2 * ttl - 1
        client.get("/")
        replacement = client.cookies.get("damwatch_session")

    assert replacement != original


def test_websocket_lookup_does_not_extend_expiry(settings):
    store = SessionStore(settings)
    session = store.issue(0)
    ttl = settings.session_ttl_seconds

    assert store.lookup(session.id, ttl - 1, touch_http=False) is session
    assert store.lookup(session.id, ttl, touch_http=False) is None


def test_capacity_refuses_new_session_then_recovers_after_sweep(settings):
    store = SessionStore(replace(settings, max_sessions=1))
    first = store.issue(0)
    ttl = settings.session_ttl_seconds

    with pytest.raises(SessionCapacityError):
        store.issue(1)

    assert store.sweep(ttl) == 1
    assert store.issue(ttl).id != first.id


def test_sweep_keeps_inflight_session_until_request_finishes(settings):
    store = SessionStore(replace(settings, max_sessions=1))
    session = store.issue(0)
    session.inflight_redeems = 1
    ttl = settings.session_ttl_seconds

    assert store.sweep(ttl) == 0
    with pytest.raises(SessionCapacityError):
        store.issue(ttl)

    session.inflight_redeems = 0
    assert store.sweep(ttl) == 1
