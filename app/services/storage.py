"""Object storage client placeholder (e.g., local/MinIO/S3)."""
from __future__ import annotations


class StorageClient:
    def __init__(self, bucket: str | None = None):
        self.bucket = bucket or "images"

    def upload_file(self, local_path: str, object_name: str) -> str:  # pragma: no cover
        """Upload a file; return an object URI (placeholder)."""
        raise NotImplementedError

    def generate_presigned_url(self, object_name: str, expires_in: int = 3600) -> str:  # pragma: no cover
        raise NotImplementedError
