"""
Storage backend for MDX blog files.
Extends the existing storage backend pattern to handle MDX files.
"""

from __future__ import annotations

import re
from pathlib import Path

from django.conf import settings

from apps.console.storage_backends import (
    LocalStorageBackend,
    GCSStorageBackend,
    StorageBackend,
)


class MDXMetadata:
    """Represents parsed frontmatter metadata from an MDX file."""

    def __init__(self, data: dict):
        self.title = data.get("title", "")
        self.description = data.get("description", "")
        self.tags = data.get("tags", [])
        self.published_at = data.get("published_at")
        self.author = data.get("author", "")
        self.featured_image = data.get("featured_image")
        self.reading_time = data.get("reading_time", 0)
        self.raw_data = data


class MDXFile:
    """Represents an MDX file with its metadata and content."""

    def __init__(
        self,
        path: str,
        metadata: MDXMetadata,
        content: str,
        raw_content: str,
    ):
        self.path = path
        self.metadata = metadata
        self.content = content  # Content without frontmatter
        self.raw_content = raw_content  # Full file content including frontmatter


class MDXStorageMixin:
    """Mixin to add MDX-specific operations to storage backends."""

    @staticmethod
    def parse_mdx(raw_content: str) -> tuple[dict, str]:
        """
        Parse MDX file content to extract frontmatter and content.

        Returns:
            tuple: (metadata_dict, content_without_frontmatter)
        """
        # Check for YAML frontmatter (--- at start and end)
        frontmatter_pattern = r"^---\s*\n(.*?)\n---\s*\n(.*)$"
        match = re.match(frontmatter_pattern, raw_content, re.DOTALL)

        if not match:
            # No frontmatter found
            return {}, raw_content

        frontmatter_str = match.group(1)
        content = match.group(2)

        # Parse YAML frontmatter
        metadata = {}
        for line in frontmatter_str.split("\n"):
            if ":" in line:
                key, value = line.split(":", 1)
                key = key.strip()
                value = value.strip()

                # Handle arrays (tags)
                if value.startswith("[") and value.endswith("]"):
                    # Parse simple array
                    value = [
                        item.strip().strip('"').strip("'")
                        for item in value[1:-1].split(",")
                        if item.strip()
                    ]
                # Handle quoted strings
                elif (value.startswith('"') and value.endswith('"')) or (
                    value.startswith("'") and value.endswith("'")
                ):
                    value = value[1:-1]
                # Handle numbers
                elif value.isdigit():
                    value = int(value)

                metadata[key] = value

        return metadata, content

    @staticmethod
    def generate_mdx(metadata: dict, content: str) -> str:
        """
        Generate MDX file content from metadata and content.

        Args:
            metadata: Dictionary of frontmatter metadata
            content: Main content body

        Returns:
            str: Complete MDX file content with frontmatter
        """
        frontmatter_lines = ["---"]

        for key, value in metadata.items():
            if isinstance(value, list):
                # Format arrays
                formatted_value = "[" + ", ".join(f'"{item}"' for item in value) + "]"
            elif isinstance(value, str):
                # Quote strings
                formatted_value = f'"{value}"'
            else:
                formatted_value = str(value)

            frontmatter_lines.append(f"{key}: {formatted_value}")

        frontmatter_lines.append("---")
        frontmatter = "\n".join(frontmatter_lines)

        return f"{frontmatter}\n\n{content}"

    @staticmethod
    def calculate_reading_time(content: str) -> int:
        """
        Calculate estimated reading time in minutes.
        Assumes average reading speed of 200 words per minute.
        """
        # Remove markdown syntax for more accurate word count
        text = re.sub(r"[#*`_\[\]()]+", "", content)
        words = len(text.split())
        return max(1, round(words / 200))

    def read_mdx_file(self, path: str) -> MDXFile:
        """
        Read and parse an MDX file.

        Args:
            path: Path to the MDX file

        Returns:
            MDXFile object
        """
        raw_content, _ = self.download_file(path)
        raw_content_str = raw_content.decode("utf-8")

        metadata_dict, content = self.parse_mdx(raw_content_str)
        metadata = MDXMetadata(metadata_dict)

        return MDXFile(
            path=path,
            metadata=metadata,
            content=content,
            raw_content=raw_content_str,
        )

    def write_mdx_file(self, path: str, metadata: dict, content: str) -> None:
        """
        Write an MDX file with metadata and content.

        Args:
            path: Path where the file should be saved
            metadata: Dictionary of frontmatter metadata
            content: Main content body
        """
        # Auto-calculate reading time if not provided
        if "reading_time" not in metadata:
            metadata["reading_time"] = self.calculate_reading_time(content)

        mdx_content = self.generate_mdx(metadata, content)
        self.upload_file(path, mdx_content.encode("utf-8"), "text/markdown")

    def list_mdx_files(self, directory: str = "blog/posts") -> list[MDXFile]:
        """
        List all MDX files in a directory.

        Args:
            directory: Directory to search for MDX files

        Returns:
            List of MDXFile objects
        """
        entries = self.list_entries(directory)
        mdx_files = []

        for entry in entries:
            if not entry.is_dir and entry.name.endswith(".mdx"):
                try:
                    mdx_file = self.read_mdx_file(entry.rel_path)
                    mdx_files.append(mdx_file)
                except Exception as e:
                    # Log error but continue
                    print(f"Error reading MDX file {entry.rel_path}: {e}")

        return mdx_files


class LocalMDXStorageBackend(LocalStorageBackend, MDXStorageMixin):
    """Local filesystem storage backend with MDX support."""

    pass


class GCSMDXStorageBackend(GCSStorageBackend, MDXStorageMixin):
    """Google Cloud Storage backend with MDX support."""

    pass


def get_mdx_storage_backend() -> StorageBackend:
    """Get the appropriate MDX storage backend based on settings."""

    # Check if using GCS in production
    storages_config = getattr(settings, "STORAGES", {})
    default_backend = storages_config.get("default", {}).get("BACKEND", "")

    if "gcloud" in default_backend.lower() or "GoogleCloudStorage" in default_backend:
        # Using GCS
        bucket_name = storages_config["default"]["OPTIONS"]["bucket_name"]
        location = storages_config["default"]["OPTIONS"].get("location", "media")
        return GCSMDXStorageBackend(bucket_name, location)
    else:
        # Using local filesystem
        media_root = getattr(settings, "MEDIA_ROOT", None)
        if media_root:
            base_dir = Path(media_root)
        else:
            base_dir = Path(settings.BASE_DIR) / "media"
        return LocalMDXStorageBackend(base_dir)
