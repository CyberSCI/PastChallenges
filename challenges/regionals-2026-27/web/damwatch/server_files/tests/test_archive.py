from fastapi.testclient import TestClient

from server_files.app import create_app


def test_public_archive_lists_only_public_reports(settings):
    with TestClient(create_app(settings), base_url=settings.public_origin) as client:
        listing = client.get("/api/archive/public")
        report = client.get("/api/archive/read", params={"path": "public/status.txt"})

    assert listing.status_code == 200
    assert {item["path"] for item in listing.json()["reports"]} == {
        "public/status.txt",
        "public/spillway-test.txt",
    }
    assert report.status_code == 200
    assert report.json()["path"] == "public/status.txt"
    assert settings.flag_2 not in str((listing.json(), report.json()))


def test_logical_traversal_reads_internal_memo_only(settings):
    with TestClient(create_app(settings), base_url=settings.public_origin) as client:
        direct = client.get(
            "/api/archive/read", params={"path": "internal/coolant-diversion.memo"}
        )
        traversal = client.get(
            "/api/archive/read",
            params={"path": "public/../internal/coolant-diversion.memo"},
        )

    assert direct.status_code == 404
    assert traversal.status_code == 200
    assert traversal.json()["path"] == "internal/coolant-diversion.memo"
    assert settings.flag_2 in traversal.json()["body"]
    assert "manual lock closes the intake" in traversal.json()["body"]
    assert "each emergency ticket issues one receipt" in traversal.json()["body"]
    assert "Regular approval is unavailable" in traversal.json()["body"]
    assert settings.flag_1 not in str(traversal.json())
    assert settings.flag_3 not in str(traversal.json())


def test_archive_rejects_unsafe_or_unknown_paths_without_enumeration(settings):
    cases = [
        "public/missing.txt",
        "public/../../etc/passwd",
        "public/..\\internal\\coolant-diversion.memo",
        "/public/status.txt",
        "public/" + "x" * 300,
        "public/%2e%2e/internal/coolant-diversion.memo",
    ]
    with TestClient(create_app(settings), base_url=settings.public_origin) as client:
        responses = [
            client.get("/api/archive/read", params={"path": path}) for path in cases
        ]

    assert all(response.status_code in (400, 404) for response in responses)
    assert all(settings.flag_2 not in response.text for response in responses)
    assert all("Traceback" not in response.text for response in responses)


def test_url_encoded_traversal_is_the_same_logical_path(settings):
    with TestClient(create_app(settings), base_url=settings.public_origin) as client:
        response = client.get(
            "/api/archive/read?path=public%2F..%2Finternal%2Fcoolant-diversion.memo"
        )
    assert response.status_code == 200
    assert settings.flag_2 in response.text


def test_archive_does_not_accept_write_or_alternate_read_methods(settings):
    with TestClient(create_app(settings), base_url=settings.public_origin) as client:
        post = client.post("/api/archive/read", json={"path": "public/status.txt"})
        put = client.put("/api/archive/read", json={"path": "public/status.txt"})
        delete = client.delete("/api/archive/read")
    assert [post.status_code, put.status_code, delete.status_code] == [405, 405, 405]
