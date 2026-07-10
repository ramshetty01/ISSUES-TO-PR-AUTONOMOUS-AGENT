"""S3-backed artifact store.

The exact same code path runs against LocalStack (via ``AWS_ENDPOINT_URL``) and
real AWS — only the endpoint differs. boto3 is imported lazily inside
``from_config`` so the module loads without it, and an S3 client can be injected
directly (tests supply a fake; no network or boto3 required).
"""

from __future__ import annotations

from typing import Any

from ..config import WorkerConfig
from ..errors import StorageError


class S3Storage:
    """Put/get/list objects in one bucket via a boto3-style S3 client."""

    scheme = "s3"

    def __init__(self, client: Any, bucket: str) -> None:
        self._client = client
        self.bucket = bucket

    @classmethod
    def from_config(cls, config: WorkerConfig, *, client: Any | None = None) -> "S3Storage":
        if client is None:
            import boto3  # lazy: only the real/LocalStack path needs it

            client = boto3.client(
                "s3",
                endpoint_url=config.aws_endpoint_url,
                region_name=config.aws_region,
            )
        return cls(client, config.s3_artifacts_bucket)

    def ensure_bucket(self) -> None:
        """Create the bucket if missing (idempotent); used before first write."""
        try:
            self._client.create_bucket(Bucket=self.bucket)
        except Exception:  # already exists / owned — safe to ignore
            pass

    def available(self) -> bool:
        """Cheap reachability probe used to decide on the local fallback."""
        try:
            self._client.head_bucket(Bucket=self.bucket)
            return True
        except Exception:
            return False

    def put(self, key: str, data: bytes) -> str:
        self._client.put_object(Bucket=self.bucket, Key=key, Body=data)
        return f"s3://{self.bucket}/{key}"

    def get(self, key: str) -> bytes:
        try:
            resp = self._client.get_object(Bucket=self.bucket, Key=key)
        except Exception as exc:  # NoSuchKey and friends
            raise StorageError(f"artifact not found: {key!r}") from exc
        body = resp["Body"]
        data = body.read()
        return data if isinstance(data, bytes) else bytes(data)

    def exists(self, key: str) -> bool:
        try:
            self._client.head_object(Bucket=self.bucket, Key=key)
            return True
        except Exception:
            return False

    def list(self, prefix: str = "") -> list[str]:
        resp = self._client.list_objects_v2(Bucket=self.bucket, Prefix=prefix)
        return sorted(obj["Key"] for obj in resp.get("Contents", []))
