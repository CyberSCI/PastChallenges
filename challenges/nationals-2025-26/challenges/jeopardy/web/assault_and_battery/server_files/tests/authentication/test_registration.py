from django.test import Client


class TestRegistration:
    def test_user_can_register(self, client: Client, mock_iterations, db):
        register_response = client.post(
            "/api/auth/register/",
            data={"username": "username", "password": "Password123!"},
        )
        assert register_response.status_code == 201
