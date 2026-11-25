from fastapi.testclient import TestClient

from server_files.app import create_app


def test_sequential_redemption_and_reset(settings):
    with TestClient(create_app(settings), base_url=settings.public_origin) as client:
        client.get("/")
        state = client.get("/api/override/state").json()
        ticket = state["ticket"]
        first = client.post(
            "/api/approvals/redeem", json={"ticket": ticket, "slot": "A"}
        )
        second = client.post(
            "/api/approvals/redeem", json={"ticket": ticket, "slot": "B"}
        )
        reset = client.post("/api/approvals/reset")
        after = client.get("/api/override/state").json()

    assert first.status_code == 200
    assert first.json()["receipt"]
    assert first.json()["expires_in_seconds"] == 900
    assert second.status_code == 409
    assert reset.status_code == 200
    assert reset.json()["ticket"] != ticket
    assert after["receipts"] == {}
    assert "test-three" not in str((state, after, first.json(), reset.json()))


def test_redeem_and_authorize_validate_inputs(settings):
    with TestClient(create_app(settings), base_url=settings.public_origin) as client:
        client.get("/")
        state = client.get("/api/override/state").json()
        bad_slot = client.post(
            "/api/approvals/redeem", json={"ticket": state["ticket"], "slot": "C"}
        )
        bad_ticket = client.post(
            "/api/approvals/redeem", json={"ticket": "wrong", "slot": "A"}
        )
        forged = client.post(
            "/api/override/authorize", json={"receipts": {"A": "x", "B": "y"}}
        )
        missing = client.post("/api/approvals/redeem", json={})

    assert bad_slot.status_code == 400
    assert bad_ticket.status_code == 400
    assert forged.status_code == 409
    assert missing.status_code == 400


def test_api_requires_existing_session(settings):
    with TestClient(create_app(settings), base_url=settings.public_origin) as client:
        assert client.get("/api/override/state").status_code == 401
        assert client.post("/api/approvals/reset").status_code == 401
        assert (
            client.post(
                "/api/override/authorize", json={"receipts": {"A": "x", "B": "y"}}
            ).status_code
            == 401
        )
