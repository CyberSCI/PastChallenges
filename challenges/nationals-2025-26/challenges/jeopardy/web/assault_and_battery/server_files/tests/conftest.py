import os
from collections.abc import Callable
from unittest.mock import patch

import django
import pytest
import structlog
from django.conf import settings
from django.contrib.auth.models import User
from faker import Faker

from authentication.models import UserEncryptionKey


@pytest.fixture
def mock_iterations():
    from authentication import hasher as hasher_module

    """Patches ITERATIONS to 2 for speed."""
    iterations = 2
    with patch.object(hasher_module, "ITERATIONS", iterations):
        yield iterations


@pytest.fixture
def mock_pepper():
    from authentication import hasher as hasher_module

    """Patches PEPPER to a known test value."""
    pepper_value = "test-pepper"
    with patch.object(hasher_module, "PEPPER", pepper_value):
        yield pepper_value


@pytest.fixture(name="create_user")
def fixture_create_user(
    db,
    faker: Faker,
    mock_iterations: int,
    mock_pepper: str,
):

    _ = structlog.contextvars.bind_contextvars(
        pepper=mock_pepper, iterations=mock_iterations
    )

    def _create_user(is_admin: bool = False):
        username = faker.user_name()
        password = faker.password()
        user_data = User(username=username, password=password)
        user = User.objects.create_user(
            username=username, password=password, is_staff=is_admin
        )
        UserEncryptionKey.setup(user, password)
        user.save()
        return user_data

    return _create_user


@pytest.fixture(name="user")
def fixture_user(create_user: Callable[[], User]):
    return create_user()


@pytest.fixture(name="user_obj")
def fixture_user_object(user: User):
    user_obj = User.objects.get(username=user.username)
    return user_obj


@pytest.fixture(name="admin_user")
def fixture_admin_user(create_user: Callable[[bool], User]):
    return create_user(True)


@pytest.fixture(name="admin_user_obj")
def fixture_admin_user_object(admin_user: User):
    user_obj = User.objects.get(username=user.username)
    return user_obj


@pytest.fixture(name="author")
def fixture_author(create_user: Callable[[], User]):
    return create_user()


@pytest.fixture(name="author_obj")
def fixture_author_object(author: User):
    user_obj = User.objects.get(username=author.username)
    return user_obj


@pytest.fixture(name="commenter")
def fixture_commenter(create_user: Callable[[], User]):
    return create_user()


@pytest.fixture(name="commenter_obj")
def fixture_commenter_object(commenter: User):
    user_obj = User.objects.get(username=commenter.username)
    return user_obj


@pytest.fixture(autouse=True)
def fixture_log_attributes(request):
    test_name = request.node.name
    _ = structlog.contextvars.bind_contextvars(test_name=test_name)


def pytest_configure():
    """Configure Django settings before running tests."""
    _ = os.environ.setdefault("PASSWORD_PEPPER", "test-pepper")
    if not settings.configured:
        settings.configure(
            DEBUG=True,
            DATABASES={
                "default": {
                    "ENGINE": "django.db.backends.sqlite3",
                    "NAME": ":memory:",
                }
            },
            INSTALLED_APPS=[
                "django.contrib.contenttypes",
                "django.contrib.auth",
                "authentication",
            ],
            USE_TZ=True,
        )
        django.setup()
