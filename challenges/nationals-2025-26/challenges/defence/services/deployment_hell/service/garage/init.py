#!/usr/bin/env python

import asyncio
import os
import tomllib
from dataclasses import dataclass
from http import HTTPStatus
from json import JSONDecodeError
from pathlib import Path
from typing import Any

import boto3
import structlog
from botocore.config import Config as BotoConfig
from botocore.exceptions import ClientError
from httpx import AsyncClient, QueryParams, Response

logger = structlog.stdlib.get_logger("garage-init")


@dataclass
class GarageAccessKey:
    access_key: str
    secret_key: str
    s3_url: str
    region: str

    def to_env(self) -> str:
        data = {
            "AWS_ACCESS_KEY_ID": self.access_key,
            "AWS_SECRET_ACCESS_KEY": self.secret_key,
            "AWS_ENDPOINT_URL": self.s3_url,
            "AWS_DEFAULT_REGION": self.region,
        }
        content = "\n".join([f"{k}={v}" for k, v in data.items()])
        return content

    @classmethod
    def from_env(cls, path: os.PathLike[str]) -> "GarageAccessKey | None":
        try:
            with open(path) as in_fd:
                lines = in_fd.read().splitlines()
                print(lines)
            vars = {
                pair[0].strip(): pair[1].strip()
                for pair in [x.split("=") for x in lines if x.strip() != ""]
            }
            access_key = vars.get("AWS_ACCESS_KEY_ID", "")
            secret_key = vars.get("AWS_SECRET_ACCESS_KEY", "")
            s3_url = vars.get("AWS_ENDPOINT_URL", "")
            region = vars.get("AWS_DEFAULT_REGION", "")
            return cls(
                access_key=access_key,
                secret_key=secret_key,
                s3_url=s3_url,
                region=region,
            )
        except FileNotFoundError:
            logger.error("File does not exist", path=str(path))
            return None


class InitClient:
    GARAGE_HOST: str = "garage"
    GARAGE_ADMIN_PORT: str = "3902"
    GARAGE_S3_PORT: str = "3900"
    GARAGE_REGION: str = "garage"

    RETRY_SECONDS: int = 5

    admin_token: str

    @property
    def admin_url(self):
        return f"http://{self.GARAGE_HOST}:{self.GARAGE_ADMIN_PORT}"

    @property
    def s3_url(self):
        return f"http://{self.GARAGE_HOST}:{self.GARAGE_S3_PORT}"

    def __init__(self):
        with open("/garage/garage.toml", "rb") as garage_config_fd:
            garage_config = tomllib.load(garage_config_fd)
        self.admin_token = garage_config["admin"]["admin_token"]

    def _admin_client(self):
        return AsyncClient(
            base_url=self.admin_url,
            headers={"Authorization": f"Bearer {self.admin_token}"},
        )

    async def _process_response(
        self,
        response: Response,
        expected_status_code: HTTPStatus,
        fail_silent: bool = False,
    ):
        log = logger.bind(
            status_code=response.status_code,
            request_url=str(response.request.url),
        )
        if response.status_code == expected_status_code:
            return response
        response_data = None
        try:
            response_data = response.json()
            log = log.bind(**response_data)
        except JSONDecodeError:
            response_data = response.text
            log = log.bind(response_data=response_data)
        if not fail_silent:
            await log.awarning("Request failed.")
        return response

    async def _admin_get(
        self,
        endpoint: str,
        params: QueryParams | None = None,
        expected_status_code: HTTPStatus = HTTPStatus.OK,
        fail_silent: bool = False,
    ):
        async with self._admin_client() as client:
            response = await client.get(endpoint, params=params)
            return await self._process_response(
                response, expected_status_code, fail_silent=fail_silent
            )

    async def _admin_post(
        self,
        endpoint: str,
        data: dict[str, Any],
        params: QueryParams | None = None,
        expected_status_code: HTTPStatus = HTTPStatus.OK,
        fail_silent: bool = False,
    ):
        async with self._admin_client() as client:
            response = await client.post(endpoint, json=data, params=params)
            return await self._process_response(
                response, expected_status_code, fail_silent=fail_silent
            )

    async def health_check(self):
        garage_healthy = False
        while not garage_healthy:
            response = await self._admin_get("/v2/GetClusterHealth")
            if response.status_code != HTTPStatus.OK:
                await logger.awarning(
                    "Health check failed. Retrying in %s seconds...",
                    self.RETRY_SECONDS,
                )
                await asyncio.sleep(self.RETRY_SECONDS)
                continue
            await logger.ainfo("Health check successful.")

            garage_healthy = True

    async def create_layout(self):
        cluster_status_response = await self._admin_get("/v2/GetClusterStatus")
        node_id = cluster_status_response.json()["nodes"][0]["id"]

        data: dict[str, object] = {
            "roles": [
                {
                    "capacity": 1073741824,
                    "tags": [],
                    "zone": "dc1",
                    "id": node_id,
                }
            ]
        }
        layout_response = await self._admin_post(
            "/v2/UpdateClusterLayout", data
        )

        if layout_response.status_code != HTTPStatus.OK:
            await logger.aerror("Cluster layout update failed.")
            return
        new_layout_version = int(layout_response.json()["version"]) + 1
        apply_response = await self._admin_post(
            "/v2/ApplyClusterLayout", data={"version": new_layout_version}
        )
        if apply_response.status_code != HTTPStatus.OK:
            await logger.aerror("Cluster layout update application failed.")
            return
        await logger.ainfo("Cluster layout updated successfully.")

    async def create_key(self, name: str, never_expires: bool = False):
        key_response = await self._admin_post(
            "/v2/CreateKey", {"name": name, "neverExpires": never_expires}
        )
        if key_response.status_code != HTTPStatus.OK:
            await logger.aerror("Key creation failed.")
            return None

        response_data = key_response.json()

        await logger.ainfo("Key created.")

        return GarageAccessKey(
            access_key=response_data["accessKeyId"],
            secret_key=response_data["secretAccessKey"],
            s3_url=self.s3_url,
            region=self.GARAGE_REGION,
        )

    async def get_or_create_bucket(
        self,
        name: str,
        access_key: GarageAccessKey | None = None,
        read: bool = False,
        write: bool = False,
    ):
        # first, look up the bucket

        bucket_response = await self._admin_get(
            "/v2/GetBucketInfo",
            params=QueryParams(globalAlias=name),
            fail_silent=True,
        )

        _ = structlog.contextvars.bind_contextvars(name=name)
        if bucket_response.status_code == HTTPStatus.OK:
            bucket_id = bucket_response.json()["id"]
            await logger.ainfo("Found existing bucket.", bucket_id=bucket_id)

            structlog.contextvars.unbind_contextvars("name")
            return bucket_id

        data: dict[str, object] = {"globalAlias": name}
        if access_key is not None:
            data["localAlias"] = {
                "accessKeyId": access_key.access_key,
                "alias": name,
                "allow": {"read": read, "write": write},
            }
        _ = structlog.contextvars.bind_contextvars(read=read, write=write)
        if access_key is not None:
            _ = structlog.contextvars.bind_contextvars(
                access_key=access_key.access_key
            )
        await logger.adebug("Creating bucket.")
        bucket_response = await self._admin_post("/v2/CreateBucket", data)
        if bucket_response.status_code != HTTPStatus.OK:
            await logger.aerror("Bucket creation failed.")
            structlog.contextvars.unbind_contextvars(
                "name", "read", "write", "access_key"
            )
            return None
        bucket_id = bucket_response.json()["id"]
        await logger.ainfo("Bucket initialized.", bucket_id=bucket_id)
        structlog.contextvars.unbind_contextvars(
            "name", "read", "write", "access_key"
        )
        return bucket_id

    async def allow_bucket_key(
        self,
        access_key: GarageAccessKey,
        bucket_id: str,
        read: bool,
        write: bool,
    ):
        response = await self._admin_post(
            "/v2/AllowBucketKey",
            {
                "bucketId": bucket_id,
                "accessKeyId": access_key.access_key,
                "permissions": {"read": read, "write": write},
            },
        )
        if response.status_code != HTTPStatus.OK:
            await logger.awarning(
                "Failed to allow access key.",
                access_key=access_key,
                bucket_id=bucket_id,
            )
            return False
        await logger.ainfo("Bucket access updated.")
        return True

    async def add_website_access(self, bucket_id: str):
        _ = structlog.contextvars.bind_contextvars(bucket_id=bucket_id)
        bucket_response = await self._admin_post(
            "/v2/UpdateBucket",
            data={
                "websiteAccess": {
                    "enabled": True,
                    "indexDocument": "index.html",
                }
            },
            params=QueryParams(id=bucket_id),
        )
        if bucket_response.status_code == HTTPStatus.NOT_FOUND:
            await logger.awarning("Could not find the bucket.")
            return False
        if bucket_response.status_code != HTTPStatus.OK:
            await logger.aerror(
                "Error updating bucket website access.",
                **bucket_response.json(),
            )
            return False

        await logger.ainfo("Bucket website access updated.")
        structlog.contextvars.unbind_contextvars("bucket_id")
        return True


def upload_file(key: GarageAccessKey, file_name: os.PathLike[str], bucket: str):
    try:
        object_name = os.path.basename(file_name)

        s3_config = BotoConfig(region_name=key.region)
        s3_client = boto3.client(
            "s3",
            config=s3_config,
            aws_access_key_id=key.access_key,
            aws_secret_access_key=key.secret_key,
            endpoint_url=key.s3_url,
        )
        response = s3_client.upload_file(file_name, bucket, object_name)
        logger.info(
            "Uploaded file.", file_name=file_name, object_name=object_name
        )
        return True
    except ClientError:
        logger.exception("Error trying to upload file.")
        return False


async def get_or_create_key(
    key_name: str, path: os.PathLike[str], init_client: InitClient
):
    key = GarageAccessKey.from_env(path)
    if key is None:
        key = await init_client.create_key(key_name, True)
    if key is None:
        await logger.aerror("Could not create key, aborting.")
        return None
    with (
        open(path, "w+") as creds_fd,
    ):
        _ = creds_fd.write(key.to_env())
    return key


async def main():
    shared = Path("/shared")
    garage_creds_path = shared / "garage-creds.env"
    jenkins_creds_path = shared / "jenkins-config-creds.env"

    init_client = InitClient()
    await init_client.health_check()
    await init_client.create_layout()

    docker_key_task = get_or_create_key(
        "docker-images", garage_creds_path, init_client
    )
    config_key_task = get_or_create_key(
        "config", jenkins_creds_path, init_client
    )

    docker_key = await docker_key_task
    config_key = await config_key_task

    if config_key is None or docker_key is None:
        await logger.aerror("Key creation failed.")
        return

    docker_image_bucket_id = await init_client.get_or_create_bucket(
        "docker-images", docker_key, read=True, write=True
    )
    config_bucket_id = await init_client.get_or_create_bucket("config")
    if config_bucket_id is not None:
        _ = await init_client.add_website_access(config_bucket_id)
        _ = await init_client.allow_bucket_key(
            config_key, config_bucket_id, True, True
        )

    upload_file(config_key, Path("/garage/jenkins.yaml"), "config")

    await logger.ainfo("Initialization complete.")


asyncio.run(main())
