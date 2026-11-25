import asyncio
import json
import time
from collections.abc import Callable
from contextlib import asynccontextmanager, suppress
from dataclasses import asdict
from pathlib import Path

from fastapi import FastAPI, Request, Response, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from starlette.requests import ClientDisconnect

from .archive import Archive, InvalidReportPath, ReportNotFound
from .config import Settings
from .state import (
    InvalidSessionError,
    InvalidTicketError,
    ObserverSession,
    RedeemCapacityError,
    RedeemRateError,
    ResetCooldownError,
    SessionCapacityError,
    SessionStore,
    SocketCapacityError,
    TicketChangedError,
    TicketUsedError,
)

COOKIE_NAME = "damwatch_session"


def create_app(
    settings: Settings,
    clock: Callable[[], float] = time.monotonic,
    audit_wait: Callable | None = None,
) -> FastAPI:
    store = SessionStore(settings, clock=clock, audit_wait=audit_wait)
    archive = Archive(settings.flag_2)

    @asynccontextmanager
    async def lifespan(_app: FastAPI):
        async def sweep_sessions():
            while True:
                await asyncio.sleep(settings.sweep_interval_seconds)
                store.sweep(clock())

        sweep_task = asyncio.create_task(sweep_sessions())
        try:
            yield
        finally:
            sweep_task.cancel()
            with suppress(asyncio.CancelledError):
                await sweep_task

    app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None, lifespan=lifespan)
    app.state.settings = settings
    app.state.clock = clock
    app.state.store = store
    app.state.archive = archive
    static_dir = Path(__file__).parent / "static"
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

    def attach_http_session(request: Request, response: Response) -> ObserverSession:
        now = clock()
        session_id = request.cookies.get(COOKIE_NAME, "")
        session = store.lookup(session_id, now, touch_http=True)
        if session is None:
            session = store.issue(now)
        response.set_cookie(
            COOKIE_NAME,
            session.id,
            max_age=settings.session_ttl_seconds,
            httponly=True,
            secure=settings.public_origin.startswith("https://"),
            samesite="lax",
        )
        return session

    app.state.attach_http_session = attach_http_session

    def existing_http_session(request: Request) -> ObserverSession | None:
        return store.lookup(
            request.cookies.get(COOKIE_NAME, ""), clock(), touch_http=True
        )

    def session_json(
        session: ObserverSession, payload: dict, status_code: int = 200
    ) -> JSONResponse:
        response = JSONResponse(payload, status_code=status_code)
        response.set_cookie(
            COOKIE_NAME,
            session.id,
            max_age=settings.session_ttl_seconds,
            httponly=True,
            secure=settings.public_origin.startswith("https://"),
            samesite="lax",
        )
        return response

    def no_session() -> JSONResponse:
        return JSONResponse(
            {
                "error": "session_required",
                "message": "Open the DamWatch console first.",
            },
            status_code=401,
        )

    async def json_object(request: Request) -> dict | None:
        try:
            body = bytearray()
            async for chunk in request.stream():
                if len(body) + len(chunk) > 4096:
                    return None
                body.extend(chunk)
            value = json.loads(body)
        except (ValueError, UnicodeDecodeError, ClientDisconnect):
            return None
        return value if isinstance(value, dict) else None

    @app.get("/healthz")
    def healthz() -> dict[str, str]:
        return {"status": "ok"}

    def page_response(request: Request, filename: str):
        response = FileResponse(
            static_dir / filename, media_type="text/html; charset=utf-8"
        )
        try:
            attach_http_session(request, response)
        except SessionCapacityError:
            return JSONResponse(
                {"error": "busy", "message": "The console is busy. Try again shortly."},
                status_code=503,
            )
        return response

    @app.get("/")
    async def live_page(request: Request):
        return page_response(request, "index.html")

    @app.get("/reports")
    async def reports_page(request: Request):
        return page_response(request, "reports.html")

    @app.get("/override")
    async def override_page(request: Request):
        return page_response(request, "override.html")

    @app.get("/api/topics")
    async def topics(request: Request):
        response = JSONResponse(
            {
                "topics": [
                    {"name": "water/level", "access": "public"},
                    {"name": "operations/triage", "access": "restricted"},
                ]
            }
        )
        try:
            attach_http_session(request, response)
        except SessionCapacityError:
            return JSONResponse(
                {"error": "busy", "message": "The console is busy. Try again shortly."},
                status_code=503,
            )
        return response

    @app.get("/api/archive/public")
    async def public_reports(request: Request):
        response = JSONResponse(
            {"reports": [asdict(report) for report in archive.list_public()]}
        )
        try:
            attach_http_session(request, response)
        except SessionCapacityError:
            return JSONResponse({"error": "busy"}, status_code=503)
        return response

    @app.get("/api/archive/read")
    async def read_report(request: Request, path: str | None = None):
        try:
            if path is None:
                raise InvalidReportPath
            report = archive.read(path)
            response = JSONResponse(asdict(report))
        except InvalidReportPath:
            response = JSONResponse({"error": "invalid_path"}, status_code=400)
        except ReportNotFound:
            response = JSONResponse({"error": "report_not_found"}, status_code=404)
        try:
            attach_http_session(request, response)
        except SessionCapacityError:
            return JSONResponse({"error": "busy"}, status_code=503)
        return response

    @app.get("/api/override/state")
    async def override_state(request: Request):
        session = existing_http_session(request)
        if session is None:
            return no_session()
        receipts = {
            receipt.slot: value
            for value, receipt in session.receipts.items()
            if receipt.generation == session.ticket.generation
            and clock() - receipt.issued_at < settings.receipt_ttl_seconds
        }
        return session_json(
            session,
            {
                "ticket": session.ticket.value,
                "generation": session.ticket.generation,
                "ticket_used": session.ticket.used,
                "receipts": receipts,
                "locked": session.lock_engaged,
            },
        )

    @app.post("/api/approvals/redeem")
    async def redeem_approval(request: Request):
        session = existing_http_session(request)
        if session is None:
            return no_session()
        body = await json_object(request)
        if (
            body is None
            or not isinstance(body.get("ticket"), str)
            or body.get("slot") not in ("A", "B")
        ):
            return session_json(
                session,
                {
                    "error": "invalid_request",
                    "message": "Enter a ticket and slot A or B.",
                },
                400,
            )
        try:
            receipt = await store.redeem(
                session.id, body["ticket"], body["slot"], clock()
            )
        except InvalidTicketError:
            return session_json(
                session,
                {"error": "invalid_ticket", "message": "This ticket is not current."},
                400,
            )
        except TicketUsedError:
            return session_json(
                session,
                {
                    "error": "ticket_used",
                    "message": "This ticket was already redeemed. Reset it to try again.",
                },
                409,
            )
        except TicketChangedError:
            return session_json(
                session,
                {
                    "error": "ticket_changed",
                    "message": "The ticket changed during review.",
                },
                409,
            )
        except RedeemRateError:
            return session_json(
                session,
                {"error": "rate_limit", "message": "Wait before trying again."},
                429,
            )
        except RedeemCapacityError:
            return session_json(
                session, {"error": "busy", "message": "Approval review is busy."}, 503
            )
        except InvalidSessionError:
            return no_session()
        return session_json(
            session,
            {
                "receipt": receipt,
                "slot": body["slot"],
                "expires_in_seconds": settings.receipt_ttl_seconds,
            },
        )

    @app.post("/api/approvals/reset")
    async def reset_approvals(request: Request):
        session = existing_http_session(request)
        if session is None:
            return no_session()
        try:
            ticket = store.reset(session.id, clock())
        except ResetCooldownError:
            return session_json(
                session,
                {
                    "error": "reset_cooldown",
                    "message": "Wait briefly before resetting again.",
                },
                409,
            )
        return session_json(
            session, {"ticket": ticket.value, "generation": ticket.generation}
        )

    @app.post("/api/override/authorize")
    async def authorize_override(request: Request):
        session = existing_http_session(request)
        if session is None:
            return no_session()
        body = await json_object(request)
        receipts = body.get("receipts") if body else None
        if not isinstance(receipts, dict) or not all(
            isinstance(receipts.get(slot), str) for slot in ("A", "B")
        ):
            return session_json(
                session,
                {
                    "error": "invalid_request",
                    "message": "Supply both approval receipts.",
                },
                400,
            )
        if not store.authorize(session.id, receipts["A"], receipts["B"], clock()):
            return session_json(
                session,
                {
                    "error": "approval_rejected",
                    "message": "Both approvals must match this ticket.",
                },
                409,
            )
        return session_json(
            session,
            {
                "locked": True,
                "message": "Manual lock engaged. Cooling Annex intake closed.",
                "flag": settings.flag_3,
            },
        )

    @app.websocket("/ws/telemetry")
    async def telemetry(websocket: WebSocket):
        origin = websocket.headers.get("origin")
        if origin is not None and origin != settings.public_origin:
            await websocket.close(code=1008)
            return
        session = store.lookup(
            websocket.cookies.get(COOKIE_NAME, ""), clock(), touch_http=False
        )
        if session is None:
            await websocket.close(code=1008)
            return
        try:
            store.open_socket(session)
        except SocketCapacityError:
            await websocket.close(code=1013)
            return

        await websocket.accept()
        try:
            while True:
                try:
                    raw = await asyncio.wait_for(
                        websocket.receive_text(), timeout=settings.ws_idle_seconds
                    )
                except TimeoutError:
                    await websocket.close(code=1000)
                    break
                except WebSocketDisconnect:
                    break

                if len(raw.encode("utf-8")) > settings.max_ws_message_bytes:
                    await websocket.close(code=1009)
                    break
                try:
                    message = json.loads(raw)
                except json.JSONDecodeError:
                    await websocket.close(code=1003)
                    break
                if store.lookup(session.id, clock(), touch_http=False) is None:
                    await websocket.close(code=1008)
                    break
                if (
                    not isinstance(message, dict)
                    or message.get("action") != "subscribe"
                ):
                    await websocket.send_json({"error": "unknown_action"})
                    continue
                topic = message.get("topic")
                if topic == "water/level":
                    await websocket.send_json(
                        {
                            "topic": "water/level",
                            "type": "snapshot",
                            "baseline_cm": 100,
                            "waterline_cm": 59,
                            "public_status": "NORMAL",
                        }
                    )
                elif topic == "operations/triage":
                    # Deliberate challenge flaw: session presence is checked, topic permission is not.
                    await websocket.send_json(
                        {
                            "topic": "operations/triage",
                            "type": "incident",
                            "id": "INC-017",
                            "message": "Unexpected drawdown. Cooling Annex diversion is open; public warning held by maintenance automation. Inspector's record: coolant-diversion.memo.",
                            "memo": "coolant-diversion.memo",
                            "flag": settings.flag_1,
                        }
                    )
                else:
                    await websocket.send_json({"error": "unknown_topic"})
        finally:
            store.close_socket(session)

    return app


def build_app() -> FastAPI:
    from .config import load_settings_from_env

    return create_app(load_settings_from_env())
