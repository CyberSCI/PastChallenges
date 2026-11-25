from fastapi.testclient import TestClient

from server_files.app import create_app


def test_three_pages_have_navigation_and_no_secret(settings):
    with TestClient(create_app(settings), base_url=settings.public_origin) as client:
        pages = [client.get(path) for path in ("/", "/reports", "/override")]

    for page in pages:
        assert page.status_code == 200
        assert page.headers["content-type"].startswith("text/html")
        assert (
            page.text.index('href="/"')
            < page.text.index('href="/reports"')
            < page.text.index('href="/override"')
        )
        assert all(
            flag not in page.text
            for flag in (settings.flag_1, settings.flag_2, settings.flag_3)
        )
    assert "03:14" in pages[0].text
    assert "North spillway test · Public status: NORMAL" in pages[0].text


def test_static_assets_are_explicit_and_flag_free(settings):
    with TestClient(create_app(settings), base_url=settings.public_origin) as client:
        script = client.get("/static/app.js")
        css = client.get("/static/style.css")
        blocked = [
            client.get(path)
            for path in (
                "/static/",
                "/server_files/app.py",
                "/solve_files/solve.py",
                "/static/app.js.map",
                "/static/../config.py",
            )
        ]

    assert script.status_code == css.status_code == 200
    assert '"water/level"' in script.text
    assert "operations/triage" not in script.text
    assert "coolant-diversion.memo" not in script.text
    assert "wss:" in script.text
    assert all(
        flag not in script.text + css.text
        for flag in (settings.flag_1, settings.flag_2, settings.flag_3)
    )
    assert all(response.status_code in (404, 405) for response in blocked)
