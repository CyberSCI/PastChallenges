from fastapi.testclient import TestClient

from server_files.app import create_app


def test_passive_response_inventory_has_no_flags(settings):
    app = create_app(settings)
    with TestClient(app, base_url=settings.public_origin) as client:
        client.get("/")
        responses = [
            client.get(path)
            for path in (
                "/",
                "/reports",
                "/override",
                "/healthz",
                "/api/topics",
                "/api/archive/public",
                "/api/archive/read?path=public/status.txt",
                "/api/override/state",
                "/static/app.js",
                "/static/style.css",
                "/docs",
                "/redoc",
                "/openapi.json",
                "/not-a-route",
            )
        ]
        responses += [
            client.post(
                "/api/override/authorize",
                json={"receipts": {"A": "forged", "B": "forged"}},
            ),
            client.post("/api/archive/read", json={"path": "public/status.txt"}),
            client.get("/api/archive/read?path=internal/coolant-diversion.memo"),
            client.get("/api/archive/read"),
        ]

    content = "\n".join(response.text for response in responses)
    assert all(
        flag not in content
        for flag in (settings.flag_1, settings.flag_2, settings.flag_3)
    )
    assert "Traceback" not in content
    assert responses[-1].status_code == 400


def test_only_intended_memo_contains_second_flag(settings):
    with TestClient(create_app(settings), base_url=settings.public_origin) as client:
        hidden = client.get(
            "/api/archive/read",
            params={"path": "public/../internal/coolant-diversion.memo"},
        )
    assert hidden.status_code == 200
    assert settings.flag_2 in hidden.text
    assert settings.flag_1 not in hidden.text
    assert settings.flag_3 not in hidden.text


def test_oversized_approval_body_is_bounded(settings):
    with TestClient(create_app(settings), base_url=settings.public_origin) as client:
        client.get("/")
        response = client.post(
            "/api/approvals/redeem",
            json={"ticket": "x" * 10000, "slot": "A"},
        )
    assert response.status_code == 400
    assert "Traceback" not in response.text
