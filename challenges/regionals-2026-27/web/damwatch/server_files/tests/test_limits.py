import asyncio
from dataclasses import replace

import pytest
from fastapi.testclient import TestClient

from server_files.app import create_app
from server_files.state import RedeemCapacityError, SessionStore


def test_redeem_rate_limit_counts_used_ticket_attempts(settings):
    limited = replace(settings, redeem_rate_per_minute=2)
    with TestClient(create_app(limited), base_url=limited.public_origin) as client:
        client.get("/")
        ticket = client.get("/api/override/state").json()["ticket"]
        results = [
            client.post("/api/approvals/redeem", json={"ticket": ticket, "slot": "A"})
            for _ in range(3)
        ]
        reset = client.post("/api/approvals/reset")

    assert [response.status_code for response in results] == [200, 409, 429]
    assert reset.status_code == 200


def test_session_capacity_recovers_after_expiry(settings):
    now = 0.0
    limited = replace(settings, max_sessions=2)
    app = create_app(limited, clock=lambda: now)
    with (
        TestClient(app, base_url=limited.public_origin) as a,
        TestClient(app, base_url=limited.public_origin) as b,
        TestClient(app, base_url=limited.public_origin) as c,
    ):
        assert a.get("/").status_code == 200
        assert b.get("/").status_code == 200
        assert c.get("/").status_code == 503
        now = limited.session_ttl_seconds
        assert c.get("/").status_code == 200


def test_forwarded_for_header_does_not_share_or_bypass_session_limit(settings):
    limited = replace(settings, max_sessions=1)
    app = create_app(limited)
    with (
        TestClient(app, base_url=limited.public_origin) as a,
        TestClient(app, base_url=limited.public_origin) as b,
    ):
        first = a.get("/", headers={"x-forwarded-for": "1.2.3.4"})
        second = b.get("/", headers={"x-forwarded-for": "1.2.3.4"})
        spoof = b.get("/", headers={"x-forwarded-for": "5.6.7.8"})
    assert first.status_code == 200
    assert second.status_code == spoof.status_code == 503


@pytest.mark.asyncio
async def test_four_pending_redemptions_are_bounded_and_released(settings):
    entered = 0
    all_entered = asyncio.Event()
    release = asyncio.Event()

    async def wait():
        nonlocal entered
        entered += 1
        if entered == 4:
            all_entered.set()
        await release.wait()

    store = SessionStore(settings, clock=lambda: 0.0, audit_wait=wait)
    session = store.issue(0)
    pending = [
        asyncio.create_task(store.redeem(session.id, session.ticket.value, "A", 0))
        for _ in range(4)
    ]
    await asyncio.wait_for(all_entered.wait(), 1)
    with pytest.raises(RedeemCapacityError):
        await store.redeem(session.id, session.ticket.value, "B", 0)
    release.set()
    receipts = await asyncio.gather(*pending)
    assert len(set(receipts)) == 4
    assert store.inflight_redeems_total == 0
    assert session.inflight_redeems == 0


@pytest.mark.asyncio
async def test_cancelled_redeem_releases_capacity(settings):
    entered = asyncio.Event()

    async def wait():
        entered.set()
        await asyncio.Event().wait()

    store = SessionStore(settings, clock=lambda: 0.0, audit_wait=wait)
    session = store.issue(0)
    pending = asyncio.create_task(
        store.redeem(session.id, session.ticket.value, "A", 0)
    )
    await asyncio.wait_for(entered.wait(), 1)
    pending.cancel()
    with pytest.raises(asyncio.CancelledError):
        await pending
    assert store.inflight_redeems_total == 0
    assert session.inflight_redeems == 0
    assert store.reset(session.id, 0).generation == 2
