"""
Storage backend abstraction for file manager.
Supports both local filesystem and Google Cloud Storage.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Protocol

from django.conf import settings
from django.utils import timezone


@dataclass
class FileEntry:
    """Represents a file or directory entry."""

    name: str
    rel_path: str
    is_dir: bool
    size: int | None
    modified: datetime
    url: str | None = None


class StorageBackend(Protocol):
    """Protocol for storage backends."""

    def exists(self, path: str = "") -> bool:
        """Check if path exists."""
        ...

    def list_entries(self, path: str = "") -> list[FileEntry]:
        """List all entries in the given path."""
        ...

    def delete(self, path: str) -> None:
        """Delete a file or directory."""
        ...

    def create_directory(self, path: str) -> None:
        """Create a new directory."""
        ...

    def upload_file(
        self, path: str, file_content: bytes, content_type: str = None
    ) -> None:
        """Upload a file."""
        ...

    def download_file(self, path: str) -> tuple[bytes, str]:
        """Download a file. Returns (content, content_type)."""
        ...

    def get_parent_path(self, path: str) -> str | None:
        """Get parent path, or None if at root."""
        ...


class LocalStorageBackend:
    """Local filesystem storage backend."""

    def __init__(self, base_dir: Path, base_url: str | None = None):
        self.base_dir = base_dir
        self.base_url = (base_url or "").strip() or None

    def exists(self, path: str = "") -> bool:
        full_path = self._resolve_path(path)
        return full_path.exists()

    def list_entries(self, path: str = "") -> list[FileEntry]:
        full_path = self._resolve_path(path)
        if not full_path.exists() or not full_path.is_dir():
            return []

        entries = []
        for entry in sorted(
            full_path.iterdir(), key=lambda p: (not p.is_dir(), p.name.lower())
        ):
            stat = entry.stat()
            rel_path = str(entry.relative_to(self.base_dir)).replace("\\", "/")

            entries.append(
                FileEntry(
                    name=entry.name,
                    rel_path=rel_path,
                    is_dir=entry.is_dir(),
                    size=None if entry.is_dir() else stat.st_size,
                    modified=timezone.localtime(
                        datetime.fromtimestamp(
                            stat.st_mtime, tz=timezone.get_current_timezone()
                        )
                    ),
                    url=None if entry.is_dir() else self._build_url(rel_path),
                )
            )
        return entries

    def delete(self, path: str) -> None:
        import shutil

        full_path = self._resolve_path(path)
        if full_path.is_dir():
            shutil.rmtree(full_path)
        else:
            full_path.unlink()

    def create_directory(self, path: str) -> None:
        full_path = self._resolve_path(path)
        full_path.mkdir(parents=True, exist_ok=False)

    def upload_file(
        self, path: str, file_content: bytes, content_type: str = None
    ) -> None:
        full_path = self._resolve_path(path)
        full_path.parent.mkdir(parents=True, exist_ok=True)
        full_path.write_bytes(file_content)

    def download_file(self, path: str) -> tuple[bytes, str]:
        import mimetypes

        full_path = self._resolve_path(path)
        content = full_path.read_bytes()
        content_type = (
            mimetypes.guess_type(str(full_path))[0] or "application/octet-stream"
        )
        return content, content_type

    def get_parent_path(self, path: str) -> str | None:
        if not path:
            return None
        parts = path.rstrip("/").split("/")
        if len(parts) <= 1:
            return ""
        return "/".join(parts[:-1])

    def _resolve_path(self, relative: str) -> Path:
        from django.core.exceptions import SuspiciousFileOperation
        from django.utils._os import safe_join

        relative = (relative or "").strip().replace("\\", "/")
        if not relative:
            return self.base_dir
        try:
            resolved = Path(safe_join(str(self.base_dir), relative))
        except (SuspiciousFileOperation, ValueError):
            from django.http import Http404

            raise Http404("Invalid path")
        return resolved.resolve()

    def _build_url(self, rel_path: str) -> str | None:
        if not self.base_url:
            return None

        rel_path = rel_path.lstrip("/").replace("\\", "/")
        base_url = self.base_url

        if base_url.endswith("/"):
            url = f"{base_url}{rel_path}"
        else:
            url = f"{base_url}/{rel_path}" if rel_path else base_url

        if url.startswith("//"):
            return f"/{url.lstrip('/')}"
        return url


class GCSStorageBackend:
    """Google Cloud Storage backend."""

    def __init__(
        self, bucket_name: str, location: str = "static", base_url: str | None = None
    ):
        self.bucket_name = bucket_name
        self.location = location.strip("/")
        self.base_url = (base_url or "").strip() or None
        self._client = None
        self._bucket = None

    @property
    def client(self):
        if self._client is None:
            from google.cloud import storage

            self._client = storage.Client(
                credentials=getattr(settings, "GS_CREDENTIALS", None)
            )
        return self._client

    @property
    def bucket(self):
        if self._bucket is None:
            self._bucket = self.client.bucket(self.bucket_name)
        return self._bucket

    def _get_prefix(self, path: str = "") -> str:
        """Get the full GCS prefix including location."""
        path = path.strip("/")
        if path:
            return f"{self.location}/{path}/"
        return f"{self.location}/"

    def _get_blob_name(self, path: str) -> str:
        """Get the full blob name."""
        path = path.strip("/")
        if path:
            return f"{self.location}/{path}"
        return self.location

    def exists(self, path: str = "") -> bool:
        # GCS buckets always "exist" - we can always list them
        return True

    def list_entries(self, path: str = "") -> list[FileEntry]:
        """List entries in GCS bucket at given path."""
        prefix = self._get_prefix(path)

        # Get all blobs with this prefix
        blobs = list(
            self.client.list_blobs(self.bucket_name, prefix=prefix, delimiter="/")
        )

        entries = []
        seen_dirs = set()

        # Handle prefixes (directories)
        for page in self.client.list_blobs(
            self.bucket_name, prefix=prefix, delimiter="/"
        ).pages:
            for prefix_name in page.prefixes:
                # Remove the location prefix and trailing slash
                rel_path = prefix_name.removeprefix(f"{self.location}/").rstrip("/")
                name = rel_path.split("/")[-1]

                if name and name not in seen_dirs:
                    seen_dirs.add(name)
                    entries.append(
                        FileEntry(
                            name=name,
                            rel_path=rel_path,
                            is_dir=True,
                            size=None,
                            modified=timezone.now(),
                            url=None,
                        )
                    )

        # Handle files
        for blob in blobs:
            # Skip if it's exactly the prefix (directory marker)
            if blob.name == prefix.rstrip("/"):
                continue

            # Get relative path
            rel_path = blob.name.removeprefix(f"{self.location}/")

            # Skip if it's in a subdirectory
            if "/" in rel_path.removeprefix(path).strip("/"):
                continue

            name = rel_path.split("/")[-1]
            if name:
                # blob.updated is already timezone-aware (UTC), so just localize it
                modified_time = (
                    timezone.localtime(blob.updated) if blob.updated else timezone.now()
                )

                entries.append(
                    FileEntry(
                        name=name,
                        rel_path=rel_path,
                        is_dir=False,
                        size=blob.size,
                        modified=modified_time,
                        url=(
                            blob.public_url
                            if blob.public_url
                            else blob.generate_signed_url(
                                expiration=3600, method="GET"  # 1 hour
                            )
                        ),
                    )
                )

        # Sort: directories first, then by name
        entries.sort(key=lambda e: (not e.is_dir, e.name.lower()))
        return entries

    def delete(self, path: str) -> None:
        """Delete a file or 'directory' (all blobs with prefix)."""
        blob_name = self._get_blob_name(path)

        # Check if it's a single file
        blob = self.bucket.blob(blob_name)
        if blob.exists():
            blob.delete()
            return

        # Otherwise, treat as directory and delete all blobs with this prefix
        prefix = f"{blob_name}/"
        blobs = list(self.bucket.list_blobs(prefix=prefix))
        for blob in blobs:
            blob.delete()

    def create_directory(self, path: str) -> None:
        """Create a 'directory' by uploading an empty marker file."""
        blob_name = self._get_blob_name(path) + "/.keep"
        blob = self.bucket.blob(blob_name)
        blob.upload_from_string(b"", content_type="application/octet-stream")

    def upload_file(
        self, path: str, file_content: bytes, content_type: str = None
    ) -> None:
        """Upload a file to GCS."""
        blob_name = self._get_blob_name(path)
        blob = self.bucket.blob(blob_name)
        blob.upload_from_string(
            file_content, content_type=content_type or "application/octet-stream"
        )

    def download_file(self, path: str) -> tuple[bytes, str]:
        """Download a file from GCS."""
        blob_name = self._get_blob_name(path)
        blob = self.bucket.blob(blob_name)

        if not blob.exists():
            from django.http import Http404

            raise Http404("File not found")

        content = blob.download_as_bytes()
        content_type = blob.content_type or "application/octet-stream"
        return content, content_type

    def get_parent_path(self, path: str) -> str | None:
        """Get parent path."""
        if not path:
            return None
        parts = path.rstrip("/").split("/")
        if len(parts) <= 1:
            return ""
        return "/".join(parts[:-1])


def get_storage_backend(storage_root: str = "static") -> StorageBackend:
    """Get the appropriate storage backend based on settings."""

    storage_root = (storage_root or "static").strip().lower()
    if storage_root not in {"static", "media"}:
        storage_root = "static"

    # Check if using GCS in production
    storages_config = getattr(settings, "STORAGES", {})
    staticfiles_backend = storages_config.get("staticfiles", {}).get("BACKEND", "")

    if (
        "gcloud" in staticfiles_backend.lower()
        or "GoogleCloudStorage" in staticfiles_backend
    ):
        # Using GCS
        static_opts = storages_config.get("staticfiles", {}).get("OPTIONS", {})
        default_opts = storages_config.get("default", {}).get("OPTIONS", {})

        bucket_name = (
            static_opts.get("bucket_name")
            or default_opts.get("bucket_name")
            or getattr(settings, "GS_BUCKET_NAME", None)
        )
        if not bucket_name:
            raise RuntimeError("GCS bucket name is not configured.")

        if storage_root == "static":
            location = static_opts.get("location", "static")
            base_url = getattr(
                settings,
                "STATIC_URL",
                f"https://storage.googleapis.com/{bucket_name}/{location}/",
            )
        else:
            location = default_opts.get("location", "media")
            base_url = getattr(
                settings,
                "MEDIA_URL",
                f"https://storage.googleapis.com/{bucket_name}/{location}/",
            )

        return GCSStorageBackend(bucket_name, location, base_url=base_url)
    else:
        # Using local filesystem
        if storage_root == "static":
            static_root = getattr(settings, "STATIC_ROOT", None)
            if static_root:
                base_dir = Path(static_root)
            else:
                static_dirs = getattr(settings, "STATICFILES_DIRS", [])
                base_dir = (
                    Path(static_dirs[0])
                    if static_dirs
                    else Path(settings.BASE_DIR) / "static"
                )
            base_url = getattr(settings, "STATIC_URL", "static/")
        else:
            media_root = getattr(settings, "MEDIA_ROOT", None)
            if media_root:
                base_dir = Path(media_root)
            else:
                base_dir = Path(settings.BASE_DIR) / "media"
            base_url = getattr(settings, "MEDIA_URL", "media/")

        return LocalStorageBackend(base_dir, base_url=base_url)
