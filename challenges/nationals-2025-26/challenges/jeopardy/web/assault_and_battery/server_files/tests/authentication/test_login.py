from django.contrib.auth.models import User
from django.test import Client


class TestLogin:
    def test_user_can_login(
        self, client: Client, user: User, mock_iterations, db
    ):
        data = {"username": user.username, "password": user.password}
        login_response = client.post(
            "/api/auth/login/",
            data=data,
        )

        assert login_response.status_code == 200
