from contextlib import ExitStack
from dataclasses import replace

from fastapi.testclient import TestClient

from server_files.app import create_app


class Clock:
    def __init__(self, value: float = 0.0):
        self.value = value

    def __call__(self) -> float:
        return self.value


def test_availability_limits_bound_lockout_window(settings):
    # A session-flood lockout must self-heal quickly: short TTL plus frequent sweeps.
    assert settings.sweep_interval_seconds <= 60
    assert settings.session_ttl_seconds <= 1800


def test_fresh_player_can_use_console_under_modeled_attack(settings):
    # Models the attack after the reverse proxy's per-IP rate limit (see README):
    # one attacker IP is capped at a trickle of new sessions and sockets.
    app = create_app(settings)
    attacker_sessions = 25
    with ExitStack() as stack:
        for _ in range(attacker_sessions):
            attacker = stack.enter_context(
                TestClient(app, base_url=settings.public_origin)
            )
            attacker.get("/")
            cookie = attacker.cookies.get("damwatch_session")
            for _ in range(settings.max_ws_per_session):
                stack.enter_context(
                    attacker.websocket_connect(
                        "/ws/telemetry",
                        headers={"cookie": f"damwatch_session={cookie}"},
                    )
                )
        assert app.state.store.active_ws_total == (
            attacker_sessions * settings.max_ws_per_session
        )
        with TestClient(app, base_url=settings.public_origin) as player:
            page = player.get("/")
            cookie = player.cookies.get("damwatch_session")
            with player.websocket_connect(
                "/ws/telemetry",
                headers={"cookie": f"damwatch_session={cookie}"},
            ) as socket:
                socket.send_json({"action": "subscribe", "topic": "water/level"})
                snapshot = socket.receive_json()
            state = player.get("/api/override/state")
            redeem = player.post(
                "/api/approvals/redeem",
                json={"ticket": state.json()["ticket"], "slot": "A"},
            )
            reset = player.post("/api/approvals/reset")

    assert page.status_code == 200
    assert snapshot["topic"] == "water/level"
    assert state.status_code == 200
    assert redeem.status_code == 200
    assert reset.status_code == 200
    assert settings.flag_3 not in page.text


def test_session_cap_backstop_blocks_then_sweep_recovers(settings):
    clock = Clock()
    limited = replace(settings, max_sessions=4)
    app = create_app(limited, clock=clock)
    with ExitStack() as stack:
        attackers = [
            stack.enter_context(TestClient(app, base_url=limited.public_origin))
            for _ in range(4)
        ]
        for attacker in attackers:
            assert attacker.get("/").status_code == 200
        with TestClient(app, base_url=limited.public_origin) as victim:
            blocked = victim.get("/")
            clock.value = limited.session_ttl_seconds
            app.state.store.sweep(clock.value)
            recovered = victim.get("/")

    assert blocked.status_code == 503
    assert recovered.status_code == 200
