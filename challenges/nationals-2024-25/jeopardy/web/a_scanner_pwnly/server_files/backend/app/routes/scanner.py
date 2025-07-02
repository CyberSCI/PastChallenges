import uuid
from typing import Annotated
from urllib.parse import urljoin

import structlog
from fastapi import Depends, HTTPException
from fastapi.routing import APIRouter
from minio import Minio
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

import app.database as db
from app.config import settings
from app.files import get_minio_client, upload_qr_code
from app.schemas import QRCode, QRCodeData, ScanInput
from app.users import current_active_user

router = APIRouter()

logger = structlog.get_logger(__name__)


@router.post("/")
async def scan(
    db_session: Annotated[AsyncSession, Depends(db.get_async_session)],
    scan_input: ScanInput,
):
    qr_code_data = scan_input.to_qr_data()
    qr_code_id = qr_code_data.id
    await logger.adebug(qr_code_id)
    find_qr_code = select(db.QRCode).where(db.QRCode.id == qr_code_id)
    qr_code = await db_session.scalar(find_qr_code)
    if qr_code is None:
        raise HTTPException(
            404,
            detail="Error processing election badge data."
            "Please contact your elections officer.",
        )

    return {"code_id": qr_code_id}


@router.post("/qr_code", response_model=QRCode)
async def new_qr_code(
    user: Annotated[db.User, Depends(current_active_user)],
    db_session: Annotated[AsyncSession, Depends(db.get_async_session)],
    minio_client: Annotated[Minio, Depends(get_minio_client)],
) -> QRCode:
    qr_code_data = QRCodeData(
        email=user.email,
        first_name=user.first_name,
        last_name=user.last_name,
        national_id=user.national_id,
        date_of_birth=user.date_of_birth,
    )

    await logger.adebug(
        "QR Code data created.", qr_code_data=qr_code_data.model_dump()
    )
    qr_code = QRCode.from_qr_data(qr_code_data)
    qr_code_data_string = qr_code.model_dump().get("data")
    assert qr_code_data_string

    image_endpoint = upload_qr_code(
        qr_code_data_string.decode(), qr_code.id, minio_client
    )

    if image_endpoint is None:
        raise RuntimeError("Failed to generate image.")

    image_url = urljoin(f"http://{settings.MINIO_ENDPOINT}", image_endpoint)
    qr_code.image_url = image_url
    qr_code_record = db.QRCode(
        id=uuid.UUID(hex=qr_code.id),
        user_id=user.id,
        url=image_url or "",
    )

    db_session.add(qr_code_record)
    await db_session.commit()

    return qr_code
