import asyncio
from dataclasses import replace

import httpx
import pytest

from server_files.app import create_app


@pytest.mark.asyncio
async def test_two_http_redemptions_cross_barrier_and_authorize(settings):
    entered = 0
    both_entered = asyncio.Event()
    release = asyncio.Event()

    async def wait_for_pair():
        nonlocal entered
        entered += 1
        if entered == 2:
            both_entered.set()
        await release.wait()

    app = create_app(settings, audit_wait=wait_for_pair)
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(
        transport=transport, base_url=settings.public_origin
    ) as client:
        await client.get("/")
        ticket = (await client.get("/api/override/state")).json()["ticket"]
        a = asyncio.create_task(
            client.post("/api/approvals/redeem", json={"ticket": ticket, "slot": "A"})
        )
        b = asyncio.create_task(
            client.post("/api/approvals/redeem", json={"ticket": ticket, "slot": "B"})
        )
        await asyncio.wait_for(both_entered.wait(), 1)
        release.set()
        one, two = await asyncio.gather(a, b)
        authorized = await client.post(
            "/api/override/authorize",
            json={"receipts": {"A": one.json()["receipt"], "B": two.json()["receipt"]}},
        )
        status = await client.get("/api/override/state")

    assert one.status_code == two.status_code == 200
    assert one.json()["receipt"] != two.json()["receipt"]
    assert authorized.status_code == 200
    assert authorized.json()["flag"] == settings.flag_3
    assert (
        authorized.json()["message"]
        == "Manual lock engaged. Cooling Annex intake closed."
    )
    assert status.json()["locked"] is True
    assert settings.flag_3 not in status.text


@pytest.mark.asyncio
async def test_reset_during_wait_invalidates_old_generation(settings):
    entered = asyncio.Event()
    release = asyncio.Event()

    async def wait():
        entered.set()
        await release.wait()

    app = create_app(settings, audit_wait=wait)
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url=settings.public_origin
    ) as client:
        await client.get("/")
        ticket = (await client.get("/api/override/state")).json()["ticket"]
        pending = asyncio.create_task(
            client.post("/api/approvals/redeem", json={"ticket": ticket, "slot": "A"})
        )
        await asyncio.wait_for(entered.wait(), 1)
        reset = await client.post("/api/approvals/reset")
        release.set()
        old = await pending
        state = (await client.get("/api/override/state")).json()

    assert reset.status_code == 200
    assert old.status_code == 409
    assert state["receipts"] == {}


@pytest.mark.asyncio
async def test_session_expiry_during_wait_releases_pending_slot(settings):
    current_time = 0.0
    entered = asyncio.Event()
    release = asyncio.Event()

    async def wait():
        entered.set()
        await release.wait()

    app = create_app(settings, clock=lambda: current_time, audit_wait=wait)
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url=settings.public_origin
    ) as client:
        await client.get("/")
        ticket = (await client.get("/api/override/state")).json()["ticket"]
        pending = asyncio.create_task(
            client.post("/api/approvals/redeem", json={"ticket": ticket, "slot": "A"})
        )
        await asyncio.wait_for(entered.wait(), 1)
        current_time = settings.session_ttl_seconds
        release.set()
        result = await pending

    assert result.status_code == 401
    assert app.state.store.inflight_redeems_total == 0


@pytest.mark.asyncio
async def test_same_slot_race_cannot_authorize_and_capacity_recovers(settings):
    limited = replace(settings, max_inflight_redeems_total=2)
    entered = 0
    both_entered = asyncio.Event()
    release = asyncio.Event()

    async def wait():
        nonlocal entered
        entered += 1
        if entered == 2:
            both_entered.set()
        await release.wait()

    app = create_app(limited, audit_wait=wait)
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url=limited.public_origin
    ) as client:
        await client.get("/")
        ticket = (await client.get("/api/override/state")).json()["ticket"]
        first = asyncio.create_task(
            client.post("/api/approvals/redeem", json={"ticket": ticket, "slot": "A"})
        )
        second = asyncio.create_task(
            client.post("/api/approvals/redeem", json={"ticket": ticket, "slot": "A"})
        )
        await asyncio.wait_for(both_entered.wait(), 1)
        over_limit = await client.post(
            "/api/approvals/redeem", json={"ticket": ticket, "slot": "B"}
        )
        release.set()
        one, two = await asyncio.gather(first, second)
        denied = await client.post(
            "/api/override/authorize",
            json={"receipts": {"A": one.json()["receipt"], "B": two.json()["receipt"]}},
        )
        reset = await client.post("/api/approvals/reset")

    assert over_limit.status_code == 503
    assert one.status_code == two.status_code == 200
    assert denied.status_code == 409
    assert reset.status_code == 200
    assert app.state.store.inflight_redeems_total == 0
