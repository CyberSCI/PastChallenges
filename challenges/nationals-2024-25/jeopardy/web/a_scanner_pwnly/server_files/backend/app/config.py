import secrets
from functools import cache
from typing import Any

from pydantic import SecretBytes, SecretStr, ValidationError
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: SecretStr = SecretStr("")
    MAC_SECRET: SecretBytes = SecretBytes(secrets.token_bytes(32))
    USER_SECRET: SecretStr = SecretStr(secrets.token_urlsafe(32))

    MINIO_ENDPOINT: str = ""
    MINIO_ACCESS_KEY: SecretStr = SecretStr("")
    MINIO_SECRET_KEY: SecretStr = SecretStr("")

    QR_CODE_BUCKET: str = "qr-codes"

    def model_post_init(self, __context: Any) -> None:
        if (
            not self.DATABASE_URL
            or not self.MINIO_ENDPOINT
            or not self.MINIO_ACCESS_KEY.get_secret_value()
            or not self.MINIO_SECRET_KEY.get_secret_value()
        ):
            raise ValidationError(
                "Environment variables missing, need: "
                + ", ".join(
                    [
                        "DATABASE_URL",
                        "MINIO_ENDPOINT",
                        "MINIO_ACCESS_KEY",
                        "MINIO_SECRET_KEY",
                    ]
                )
            )

        return super().model_post_init(__context)


@cache
def get_settings():
    return Settings()


settings = get_settings()
