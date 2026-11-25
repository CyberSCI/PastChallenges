import asyncio
import secrets
import time
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field

from .config import Settings


class SessionCapacityError(Exception):
    pass


class SocketCapacityError(Exception):
    pass


class ResetCooldownError(Exception):
    pass


class InvalidSessionError(Exception):
    pass


class InvalidTicketError(Exception):
    pass


class TicketUsedError(Exception):
    pass


class TicketChangedError(Exception):
    pass


class RedeemRateError(Exception):
    pass


class RedeemCapacityError(Exception):
    pass


@dataclass
class Ticket:
    value: str
    generation: int
    issued_at: float
    used: bool = False


@dataclass(frozen=True)
class Receipt:
    session_id: str
    generation: int
    slot: str
    issued_at: float


@dataclass
class ObserverSession:
    id: str
    last_http_at: float
    ticket: Ticket
    receipts: dict[str, Receipt] = field(default_factory=dict)
    lock_engaged: bool = False
    inflight_redeems: int = 0
    active_ws_count: int = 0
    last_reset_at: float | None = None
    redeem_times: list[float] = field(default_factory=list)


class SessionStore:
    def __init__(
        self,
        settings: Settings,
        clock: Callable[[], float] = time.monotonic,
        audit_wait: Callable[[], Awaitable[None]] | None = None,
    ):
        self.settings = settings
        self.clock = clock
        self.audit_wait = audit_wait or self._default_audit_wait
        self.sessions: dict[str, ObserverSession] = {}
        self.active_ws_total = 0
        self.inflight_redeems_total = 0

    async def _default_audit_wait(self) -> None:
        await asyncio.sleep(self.settings.audit_delay_seconds)

    def issue(self, now: float) -> ObserverSession:
        self.sweep(now)
        if len(self.sessions) >= self.settings.max_sessions:
            raise SessionCapacityError
        session = ObserverSession(
            id=secrets.token_urlsafe(24),
            last_http_at=now,
            ticket=Ticket(value=secrets.token_urlsafe(24), generation=1, issued_at=now),
        )
        self.sessions[session.id] = session
        return session

    def lookup(
        self, session_id: str, now: float, *, touch_http: bool
    ) -> ObserverSession | None:
        session = self.sessions.get(session_id)
        if session is None:
            return None
        if now - session.last_http_at >= self.settings.session_ttl_seconds:
            if not session.inflight_redeems:
                self.sessions.pop(session_id, None)
            return None
        if touch_http:
            session.last_http_at = now
        return session

    def sweep(self, now: float) -> int:
        expired = [
            session_id
            for session_id, session in self.sessions.items()
            if now - session.last_http_at >= self.settings.session_ttl_seconds
            and not session.inflight_redeems
        ]
        for session_id in expired:
            self.sessions.pop(session_id, None)
        return len(expired)

    def open_socket(self, session: ObserverSession) -> None:
        if (
            session.active_ws_count >= self.settings.max_ws_per_session
            or self.active_ws_total >= self.settings.max_ws_total
        ):
            raise SocketCapacityError
        session.active_ws_count += 1
        self.active_ws_total += 1

    def close_socket(self, session: ObserverSession) -> None:
        session.active_ws_count -= 1
        self.active_ws_total -= 1

    def reset(self, session_id: str, now: float) -> Ticket:
        session = self.lookup(session_id, now, touch_http=False)
        if session is None:
            raise InvalidSessionError
        if (
            session.last_reset_at is not None
            and now - session.last_reset_at < self.settings.reset_cooldown_seconds
        ):
            raise ResetCooldownError
        session.ticket = Ticket(
            value=secrets.token_urlsafe(24),
            generation=session.ticket.generation + 1,
            issued_at=now,
        )
        session.receipts.clear()
        session.last_reset_at = now
        return session.ticket

    def issue_receipt(self, session_id: str, slot: str, now: float) -> str:
        session = self.lookup(session_id, now, touch_http=False)
        if session is None or slot not in ("A", "B"):
            raise InvalidSessionError
        value = secrets.token_urlsafe(24)
        session.receipts[value] = Receipt(
            session_id=session_id,
            generation=session.ticket.generation,
            slot=slot,
            issued_at=now,
        )
        return value

    def authorize(
        self, session_id: str, receipt_a: str, receipt_b: str, now: float
    ) -> bool:
        session = self.lookup(session_id, now, touch_http=False)
        if session is None or receipt_a == receipt_b:
            return False
        for value, slot in ((receipt_a, "A"), (receipt_b, "B")):
            receipt = session.receipts.get(value)
            if (
                receipt is None
                or receipt.session_id != session_id
                or receipt.generation != session.ticket.generation
                or receipt.slot != slot
                or now - receipt.issued_at >= self.settings.receipt_ttl_seconds
            ):
                return False
        session.lock_engaged = True
        return True

    async def redeem(
        self, session_id: str, ticket_value: str, slot: str, now: float
    ) -> str:
        session = self.lookup(session_id, now, touch_http=False)
        if session is None:
            raise InvalidSessionError
        session.redeem_times = [t for t in session.redeem_times if now - t < 60]
        if len(session.redeem_times) >= self.settings.redeem_rate_per_minute:
            raise RedeemRateError
        session.redeem_times.append(now)
        if slot not in ("A", "B") or ticket_value != session.ticket.value:
            raise InvalidTicketError
        if session.ticket.used:
            raise TicketUsedError
        if (
            session.inflight_redeems >= self.settings.max_inflight_redeems_per_session
            or self.inflight_redeems_total >= self.settings.max_inflight_redeems_total
        ):
            raise RedeemCapacityError
        generation = session.ticket.generation
        session.inflight_redeems += 1
        self.inflight_redeems_total += 1
        try:
            await self.audit_wait()
            current = self.lookup(session_id, self.clock(), touch_http=False)
            if current is None:
                raise InvalidSessionError
            if (
                current.ticket.generation != generation
                or current.ticket.value != ticket_value
            ):
                raise TicketChangedError
            # Deliberate flaw: parallel requests that passed the first used check may both finish.
            receipt = self.issue_receipt(session_id, slot, self.clock())
            current.ticket.used = True
            return receipt
        finally:
            session.inflight_redeems -= 1
            self.inflight_redeems_total -= 1
