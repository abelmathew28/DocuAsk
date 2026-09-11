from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import BinaryIO

from app.core.config import settings


class StorageBackend(ABC):
    @abstractmethod
    def save(self, user_id: str, document_id: str, filename: str, data: bytes) -> str:
        raise NotImplementedError

    @abstractmethod
    def load(self, storage_path: str) -> bytes:
        raise NotImplementedError

    @abstractmethod
    def open(self, storage_path: str) -> BinaryIO:
        raise NotImplementedError

    @abstractmethod
    def delete(self, storage_path: str) -> None:
        raise NotImplementedError


class LocalStorage(StorageBackend):
    def __init__(self, root: str | None = None) -> None:
        self.root = Path(root or settings.LOCAL_STORAGE_PATH)
        self.root.mkdir(parents=True, exist_ok=True)

    def _path(self, storage_path: str) -> Path:
        return self.root / storage_path

    def save(self, user_id: str, document_id: str, filename: str, data: bytes) -> str:
        relative = f"{user_id}/{document_id}/{filename}"
        destination = self._path(relative)
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(data)
        return relative

    def load(self, storage_path: str) -> bytes:
        return self._path(storage_path).read_bytes()

    def open(self, storage_path: str) -> BinaryIO:
        return open(self._path(storage_path), "rb")

    def delete(self, storage_path: str) -> None:
        path = self._path(storage_path)
        if path.exists():
            path.unlink()


class S3Storage(StorageBackend):
    def __init__(self) -> None:
        import boto3

        if not settings.AWS_S3_BUCKET:
            raise RuntimeError("AWS_S3_BUCKET is required when STORAGE_BACKEND=s3")
        self.bucket = settings.AWS_S3_BUCKET
        self.client = boto3.client(
            "s3",
            region_name=settings.AWS_REGION,
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID or None,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY or None,
        )

    def save(self, user_id: str, document_id: str, filename: str, data: bytes) -> str:
        key = f"users/{user_id}/documents/{document_id}/{filename}"
        self.client.put_object(
            Bucket=self.bucket,
            Key=key,
            Body=data,
            ContentType="application/pdf",
            ServerSideEncryption="AES256",
        )
        return key

    def load(self, storage_path: str) -> bytes:
        response = self.client.get_object(Bucket=self.bucket, Key=storage_path)
        return response["Body"].read()

    def open(self, storage_path: str) -> BinaryIO:
        from io import BytesIO

        return BytesIO(self.load(storage_path))

    def delete(self, storage_path: str) -> None:
        self.client.delete_object(Bucket=self.bucket, Key=storage_path)


def get_storage() -> StorageBackend:
    if settings.STORAGE_BACKEND.lower() == "s3":
        return S3Storage()
    return LocalStorage()
