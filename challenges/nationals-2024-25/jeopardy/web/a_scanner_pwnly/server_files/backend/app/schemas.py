import base64
import hmac
import pickle
import uuid
from typing import Annotated

import structlog
from fastapi_users import schemas
from pydantic import (
    Base64Bytes,
    BaseModel,
    Field,
    PastDate,
)

from app.config import settings

logger = structlog.stdlib.get_logger(__name__)


class UserRead(schemas.BaseUser[uuid.UUID]):
    pass


class UserCreate(schemas.BaseUserCreate):
    first_name: str
    last_name: str
    national_id: Annotated[str, Field(min_length=9, max_length=9)]
    date_of_birth: PastDate


class UserUpdate(schemas.BaseUserUpdate):
    first_name: str
    last_name: str
    national_id: Annotated[str | None, Field(min_length=9, max_length=9)]
    date_of_birth: PastDate | None


class QRCodeData(BaseModel):
    email: str
    first_name: str
    last_name: str
    national_id: str
    date_of_birth: PastDate

    id: Annotated[
        str | None, Field(default_factory=lambda: uuid.uuid4().hex)
    ] = None


class ScanInput(BaseModel):
    data: Base64Bytes

    def to_qr_data(self) -> QRCodeData:
        qr_code_data = pickle.loads(self.data)
        # No sense wasting code!
        qr_code = QRCode.from_qr_data(qr_code_data)

        if not hmac.compare_digest(
            hmac.digest(
                settings.MAC_SECRET.get_secret_value(), self.data, "sha256"
            ),
            qr_code.tag,
        ):
            raise ValueError("Invalid HMAC.")

        return qr_code_data


class QRCode(BaseModel):
    id: Annotated[
        str | None, Field(default_factory=lambda: uuid.uuid4().hex)
    ] = None
    data: Base64Bytes
    tag: Base64Bytes
    image_url: str | None = None

    @classmethod
    def from_qr_data(
        cls,
        qr_data: QRCodeData,
    ) -> "QRCode":
        hmac_payload = pickle.dumps(qr_data)

        data = base64.b64encode(hmac_payload)

        tag = base64.b64encode(
            hmac.digest(
                settings.MAC_SECRET.get_secret_value(),
                hmac_payload,
                "sha256",
            )
        )

        qr_code = cls(id=qr_data.id, data=data, tag=tag)

        return qr_code
