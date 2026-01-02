"""Local filesystem adapter implementing IFileSystem protocol."""

from __future__ import annotations

import shutil
from pathlib import Path


class LocalFileSystem:
    """Local filesystem implementation."""

    def create_directory(self, path: Path) -> Path:
        """Create directory and any parent directories.

        Args:
            path: Directory path to create

        Returns:
            Created directory path
        """
        path.mkdir(parents=True, exist_ok=True)
        return path

    def list_directories(self, path: Path, pattern: str) -> list[Path]:
        """List directories matching pattern.

        Args:
            path: Base directory to search
            pattern: Glob pattern to match

        Returns:
            List of matching directory paths
        """
        return [p for p in path.glob(pattern) if p.is_dir()]

    def delete_directory(self, path: Path) -> None:
        """Recursively delete directory.

        Args:
            path: Directory to delete
        """
        if path.exists():
            shutil.rmtree(path)
