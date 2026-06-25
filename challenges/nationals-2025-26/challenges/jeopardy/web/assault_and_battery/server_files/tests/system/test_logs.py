from collections.abc import Callable

import pytest
from django.contrib.auth.models import User
from django.test import Client


@pytest.fixture(name="login_client_for")
def fixture_login_client_for(db, client: Client):
    def _create_client(target_user: User):
        login_data = {
            "username": target_user.username,
            "password": target_user.password,
        }
        login_response = client.post(
            "/api/auth/login/",
            data=login_data,
        )

        assert login_response.status_code == 200

        return client

    return _create_client


@pytest.fixture(name="login_client")
def fixture_login_client(
    login_client_for: Callable[[User], Client], user: User
):
    yield login_client_for(user)


class TestLogs:
    def test_user_can_view_logs(self, login_client: Client):
        log_response = login_client.get("/api/system/logs/")

        assert log_response.status_code == 200

        assert log_response.json()["page_size"] != 0

    def test_user_can_adjust_page_size(self, login_client: Client):
        log_response = login_client.get("/api/system/logs/?size=25")

        assert log_response.status_code == 200

        assert log_response.json()["page_size"] <= 25

    # TODO: Add test for massive log sizes

    def test_user_can_request_many_logs(self, login_client: Client):
        log_response = login_client.get("/api/system/logs/?size=1000")

        assert log_response.status_code == 200

        page_size = log_response.json()["page_size"]

        assert page_size <= 1000
        assert page_size > 100
        assert page_size > 500

    def test_user_can_filter_levels(self, login_client: Client):
        log_response = login_client.get("/api/system/logs/?level=info")

        assert log_response.status_code == 200
        records = log_response.json()["records"]
        for hit in records:
            assert hit["level"] == "info"

        log_response = login_client.get("/api/system/logs/?level=invalid")
        assert log_response.status_code == 400

    def test_user_can_filter_requests(self, login_client: Client):
        log_response = login_client.get("/api/system/logs/?level=info")

        assert log_response.status_code == 200
        records = log_response.json()["records"]
        request_id = records[-1]["request_id"]

        filtered_log_response = login_client.get(
            f"/api/system/logs/?request_id={request_id}"
        )

        records = filtered_log_response.json()["records"]
        assert len(records) > 0
        for record in records:
            assert record["request_id"] == request_id

    def test_compound_filtering(self, login_client: Client):
        log_response = login_client.get("/api/system/logs/?level=info")

        assert log_response.status_code == 200
        records = log_response.json()["records"]
        request_id = records[-1]["request_id"]

        filtered_log_response = login_client.get(
            f"/api/system/logs/?request_id={request_id}&level=info"
        )

        records = filtered_log_response.json()["records"]
        assert len(records) > 0
        for record in records:
            assert record["level"] == "info"
