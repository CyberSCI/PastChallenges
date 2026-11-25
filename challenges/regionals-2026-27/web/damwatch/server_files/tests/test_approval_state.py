import pytest

from server_files.state import ResetCooldownError, SessionStore


def test_ticket_reset_rotates_generation_and_obeys_cooldown(settings):
    store = SessionStore(settings)
    session = store.issue(100)
    first = session.ticket.value
    receipt = store.issue_receipt(session.id, "A", 101)

    next_ticket = store.reset(session.id, 102)
    assert next_ticket.generation == 2
    assert next_ticket.value != first
    assert session.receipts == {}
    assert not store.authorize(session.id, receipt, receipt, 103)
    with pytest.raises(ResetCooldownError):
        store.reset(session.id, 103)
    assert store.reset(session.id, 104).generation == 3


def test_authorization_needs_matching_distinct_live_receipts(settings):
    store = SessionStore(settings)
    a = store.issue(0)
    b = store.issue(0)
    a1 = store.issue_receipt(a.id, "A", 1)
    a2 = store.issue_receipt(a.id, "A", 1)
    b1 = store.issue_receipt(a.id, "B", 1)
    other = store.issue_receipt(b.id, "B", 1)

    assert not store.authorize(a.id, "forged", b1, 2)
    assert not store.authorize(a.id, a1, a1, 2)
    assert not store.authorize(a.id, a1, a2, 2)
    assert not store.authorize(a.id, a1, other, 2)
    assert not store.authorize(b.id, a1, other, 2)
    assert not store.authorize(a.id, a1, b1, 901)
    assert not a.lock_engaged
    assert not b.lock_engaged


def test_authorization_is_session_scoped_and_idempotent(settings):
    store = SessionStore(settings)
    a = store.issue(0)
    b = store.issue(0)
    a_receipt = store.issue_receipt(a.id, "A", 1)
    b_receipt = store.issue_receipt(a.id, "B", 1)

    assert store.authorize(a.id, a_receipt, b_receipt, 2)
    assert store.authorize(a.id, a_receipt, b_receipt, 2)
    assert a.lock_engaged
    assert not b.lock_engaged


def test_reset_rejects_prior_generation_and_session_expiry(settings):
    store = SessionStore(settings)
    session = store.issue(0)
    a = store.issue_receipt(session.id, "A", 1)
    store.reset(session.id, 2)
    b = store.issue_receipt(session.id, "B", 3)
    assert not store.authorize(session.id, a, b, 4)
    assert not store.authorize(session.id, a, b, settings.session_ttl_seconds)
    assert (
        store.lookup(session.id, settings.session_ttl_seconds, touch_http=False) is None
    )
