from datetime import UTC, datetime, timedelta

import jwt
import structlog
from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist
from jwt.exceptions import InvalidTokenError

SECRET_KEY = "09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

logger = structlog.stdlib.get_logger("reclaimer_central.crypto")


def create_access_token(
    data: dict[str, object], expires_delta: timedelta | None = None
):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(UTC) + expires_delta
    else:
        expire = datetime.now(UTC) + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def get_current_user(token: str):
    credentials_exception = Exception("Could not validate credentials")
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        if username is None:
            raise credentials_exception
    except InvalidTokenError as e:
        logger.exception("JWT ERROR ENCOUNTERED")
        raise credentials_exception from e

    try:
        user = User.objects.get(username=username)
        return user
    except ObjectDoesNotExist as e:
        logger.exception("USER RETRIEVAL ERROR ENCOUNTERED")
        raise credentials_exception from e
