"""Local filesystem adapter implementing FileSystem protocol."""

from __future__ import annotations

import shutil
from pathlib import Path

from nixos_rebuild_tester.domain.exceptions import (
    DirectoryCreationFailed,
    FileSystemError,
    PathNotFound,
    PathNotWritable,
)


class LocalFileSystem:
    """Local filesystem implementation.

    Provides complete filesystem abstraction following the FileSystem protocol.
    """

    # Directory operations
    async def create_directory(self, path: Path) -> Path:
        """Create directory and parents.

        Args:
            path: Directory to create

        Returns:
            Created directory path

        Raises:
            DirectoryCreationFailed: If creation fails
        """
        try:
            path.mkdir(parents=True, exist_ok=True)
            return path
        except Exception as e:
            raise DirectoryCreationFailed(f"Failed to create directory {path}: {e}") from e

    async def delete_directory(self, path: Path) -> None:
        """Recursively delete directory.

        Args:
            path: Directory to delete

        Raises:
            FileSystemError: If deletion fails
        """
        try:
            if path.exists():
                shutil.rmtree(path)
        except Exception as e:
            raise FileSystemError(f"Failed to delete directory {path}: {e}") from e

    async def list_directories(self, base: Path, pattern: str) -> list[Path]:
        """List directories matching pattern.

        Args:
            base: Base directory to search
            pattern: Glob pattern

        Returns:
            List of matching directories
        """
        try:
            if not base.exists():
                return []
            return [p for p in base.glob(pattern) if p.is_dir()]
        except Exception as e:
            raise FileSystemError(f"Failed to list directories in {base}: {e}") from e

    def directory_exists(self, path: Path) -> bool:
        """Check if directory exists.

        Args:
            path: Directory to check

        Returns:
            True if exists and is directory
        """
        return path.exists() and path.is_dir()

    # File operations
    async def write_text(self, path: Path, content: str) -> None:
        """Write text to file.

        Args:
            path: File path
            content: Text content

        Raises:
            PathNotWritable: If write fails
        """
        try:
            path.write_text(content)
        except Exception as e:
            raise PathNotWritable(f"Failed to write to {path}: {e}") from e

    async def read_text(self, path: Path) -> str:
        """Read text from file.

        Args:
            path: File path

        Returns:
            File contents

        Raises:
            PathNotFound: If file doesn't exist
        """
        try:
            return path.read_text()
        except FileNotFoundError as e:
            raise PathNotFound(f"File not found: {path}") from e
        except Exception as e:
            raise FileSystemError(f"Failed to read {path}: {e}") from e

    async def write_bytes(self, path: Path, content: bytes) -> None:
        """Write bytes to file.

        Args:
            path: File path
            content: Byte content

        Raises:
            PathNotWritable: If write fails
        """
        try:
            path.write_bytes(content)
        except Exception as e:
            raise PathNotWritable(f"Failed to write bytes to {path}: {e}") from e

    async def read_bytes(self, path: Path) -> bytes:
        """Read bytes from file.

        Args:
            path: File path

        Returns:
            File contents

        Raises:
            PathNotFound: If file doesn't exist
        """
        try:
            return path.read_bytes()
        except FileNotFoundError as e:
            raise PathNotFound(f"File not found: {path}") from e
        except Exception as e:
            raise FileSystemError(f"Failed to read bytes from {path}: {e}") from e

    async def delete_file(self, path: Path) -> None:
        """Delete file.

        Args:
            path: File to delete

        Raises:
            FileSystemError: If deletion fails
        """
        try:
            if path.exists():
                path.unlink()
        except Exception as e:
            raise FileSystemError(f"Failed to delete file {path}: {e}") from e

    def file_exists(self, path: Path) -> bool:
        """Check if file exists.

        Args:
            path: File to check

        Returns:
            True if exists and is file
        """
        return path.exists() and path.is_file()

    # Metadata
    async def get_modified_time(self, path: Path) -> float:
        """Get modification timestamp.

        Args:
            path: Path to check

        Returns:
            Modification time as unix timestamp

        Raises:
            PathNotFound: If path doesn't exist
        """
        try:
            return path.stat().st_mtime
        except FileNotFoundError as e:
            raise PathNotFound(f"Path not found: {path}") from e
        except Exception as e:
            raise FileSystemError(f"Failed to get modification time for {path}: {e}") from e

    async def get_size(self, path: Path) -> int:
        """Get file size.

        Args:
            path: File to check

        Returns:
            Size in bytes

        Raises:
            PathNotFound: If path doesn't exist
        """
        try:
            return path.stat().st_size
        except FileNotFoundError as e:
            raise PathNotFound(f"Path not found: {path}") from e
        except Exception as e:
            raise FileSystemError(f"Failed to get size for {path}: {e}") from e
