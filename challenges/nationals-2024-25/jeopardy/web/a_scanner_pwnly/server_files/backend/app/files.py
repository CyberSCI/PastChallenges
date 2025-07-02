import tempfile
from functools import cache

import qrcode
import structlog
from minio import Minio
from urllib3 import BaseHTTPResponse

from app.config import settings

logger = structlog.stdlib.get_logger(__name__)


@cache
def get_minio_client() -> Minio:
    client = Minio(
        settings.MINIO_ENDPOINT,
        settings.MINIO_ACCESS_KEY.get_secret_value(),
        settings.MINIO_SECRET_KEY.get_secret_value(),
        secure=False,
    )

    return client


def upload_qr_code(
    qr_code_data: str,
    qr_code_id: str | None,
    minio_client: Minio,
) -> str | None:
    assert qr_code_id
    qr_code_filename = f"{qr_code_id}.png"
    bucket_name = settings.QR_CODE_BUCKET
    with tempfile.NamedTemporaryFile("+wt", suffix="png") as img_file:
        img_data = qrcode.make(qr_code_data)
        img_data.save(img_file.name)  # pyright: ignore
        found = minio_client.bucket_exists(bucket_name)
        if not found:
            minio_client.make_bucket(bucket_name)
        minio_client.fput_object(bucket_name, qr_code_filename, img_file.name)
    res: BaseHTTPResponse | None = None
    res_url: str | None = None
    try:
        res = minio_client.get_object(bucket_name, qr_code_filename)
        res_url = res.url

        logger.debug(
            "Made a request to the Minio API.",
            res_url=res_url,
        )
    finally:
        if res:
            res.close()
            res.release_conn()
    return res_url
