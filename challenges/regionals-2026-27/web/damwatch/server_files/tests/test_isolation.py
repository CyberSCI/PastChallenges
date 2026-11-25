from fastapi.testclient import TestClient

from server_files.app import create_app


def test_tickets_and_resets_are_isolated_between_clients(settings):
    app = create_app(settings)
    with (
        TestClient(app, base_url=settings.public_origin) as a,
        TestClient(app, base_url=settings.public_origin) as b,
    ):
        a.get("/")
        b.get("/")
        state_a = a.get("/api/override/state").json()
        state_b = b.get("/api/override/state").json()
        swapped = b.post(
            "/api/approvals/redeem", json={"ticket": state_a["ticket"], "slot": "A"}
        )
        own = a.post(
            "/api/approvals/redeem", json={"ticket": state_a["ticket"], "slot": "A"}
        )
        a.post("/api/approvals/reset")
        after_b = b.get("/api/override/state").json()

    assert state_a["ticket"] != state_b["ticket"]
    assert swapped.status_code == 400
    assert own.status_code == 200
    assert after_b == state_b


def test_one_clients_lock_does_not_affect_another(settings):
    app = create_app(settings)
    with (
        TestClient(app, base_url=settings.public_origin) as a,
        TestClient(app, base_url=settings.public_origin) as b,
    ):
        a.get("/")
        b.get("/")
        session_a = app.state.store.lookup(
            a.cookies["damwatch_session"], app.state.clock(), touch_http=False
        )
        receipt_a = app.state.store.issue_receipt(session_a.id, "A", app.state.clock())
        receipt_b = app.state.store.issue_receipt(session_a.id, "B", app.state.clock())
        locked = a.post(
            "/api/override/authorize",
            json={"receipts": {"A": receipt_a, "B": receipt_b}},
        )
        other = b.get("/api/override/state")
        public = b.get("/api/topics")

    assert locked.status_code == 200
    assert settings.flag_3 in locked.text
    assert other.json()["locked"] is False
    assert settings.flag_3 not in other.text + public.text
