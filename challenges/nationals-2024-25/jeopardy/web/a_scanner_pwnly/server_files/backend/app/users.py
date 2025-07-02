import uuid
from typing import Annotated

import structlog
from fastapi import Depends, Request
from fastapi_users import BaseUserManager, FastAPIUsers, UUIDIDMixin
from fastapi_users.authentication import (
    AuthenticationBackend,
    BearerTransport,
    JWTStrategy,
)
from fastapi_users.db import SQLAlchemyUserDatabase

from app.config import settings
from app.database import User, get_user_db

logger = structlog.get_logger(__name__)

AUTH_URL_PATH = "auth"


class UserManager(UUIDIDMixin, BaseUserManager[User, uuid.UUID]):
    reset_password_token_secret = settings.USER_SECRET.get_secret_value()
    verification_token_secret = settings.USER_SECRET.get_secret_value()

    async def on_after_register(
        self, user: User, request: Request | None = None
    ):
        await logger.ainfo(f"User {user.id} has registered.")

    async def on_after_forgot_password(
        self, user: User, token: str, request: Request | None = None
    ):
        await logger.ainfo(
            f"User {user.id} has forgot their password. Reset token: {token}"
        )

    async def on_after_request_verify(
        self, user: User, token: str, request: Request | None = None
    ):
        await logger.ainfo(
            f"Verification requested for user {user.id}. Verification token: {token}"
        )


async def get_user_manager(
    user_db: Annotated[SQLAlchemyUserDatabase, Depends(get_user_db)],
):
    yield UserManager(user_db)


bearer_transport = BearerTransport(tokenUrl=f"{AUTH_URL_PATH}/jwt/login")


def get_jwt_strategy() -> JWTStrategy:
    return JWTStrategy(
        secret=settings.USER_SECRET.get_secret_value(), lifetime_seconds=3600
    )


auth_backend = AuthenticationBackend(
    name="jwt",
    transport=bearer_transport,
    get_strategy=get_jwt_strategy,
)

fastapi_users = FastAPIUsers[User, uuid.UUID](get_user_manager, [auth_backend])

current_active_user = fastapi_users.current_user(active=True)
