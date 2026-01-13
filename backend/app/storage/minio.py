from functools import lru_cache

import boto3
from botocore.exceptions import ClientError

from app.config import get_settings
from app.storage.base import StorageClient


class MinioStorageClient(StorageClient):
    def __init__(self) -> None:
        settings = get_settings()
        self._bucket = settings.s3_bucket
        endpoint = settings.s3_endpoint
        if endpoint and not endpoint.startswith("http"):
            scheme = "https" if settings.s3_secure else "http"
            endpoint = f"{scheme}://{endpoint}"
        self._client = boto3.client(
            "s3",
            endpoint_url=endpoint,
            aws_access_key_id=settings.s3_access_key,
            aws_secret_access_key=settings.s3_secret_key,
            region_name=settings.s3_region,
        )
        self._ensure_bucket()

    def _ensure_bucket(self) -> None:
        try:
            self._client.head_bucket(Bucket=self._bucket)
        except ClientError:
            self._client.create_bucket(Bucket=self._bucket)

    def put_bytes(self, key: str, data: bytes, content_type: str) -> None:
        self._client.put_object(
            Bucket=self._bucket,
            Key=key,
            Body=data,
            ContentType=content_type,
        )


@lru_cache
def get_storage_client() -> StorageClient:
    return MinioStorageClient()
