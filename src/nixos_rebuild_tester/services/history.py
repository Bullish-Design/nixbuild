"""Build history management service."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from nixos_rebuild_tester.domain.value_objects import Timestamp

if TYPE_CHECKING:
    from nixos_rebuild_tester.domain.protocols import IFileSystem


class BuildHistoryManager:
    """Manages build history and cleanup."""

    def __init__(
        self,
        filesystem: IFileSystem,
        base_dir: Path,
        keep_last_n: int | None = None,
    ):
        """Initialize history manager.

        Args:
            filesystem: Filesystem implementation
            base_dir: Base directory for build outputs
            keep_last_n: Number of builds to keep (None = keep all)
        """
        self._fs = filesystem
        self._base_dir = base_dir.expanduser()
        self._keep_last_n = keep_last_n

    def create_build_directory(self) -> Path:
        """Create timestamped build directory.

        Returns:
            Path to created directory
        """
        timestamp = Timestamp()
        dir_name = f"rebuild-{timestamp.filesystem_safe}"
        output_dir = self._base_dir / dir_name

        return self._fs.create_directory(output_dir)

    async def cleanup_old_builds(self) -> list[Path]:
        """Delete old build directories beyond retention limit.

        Returns:
            List of deleted directories
        """
        if self._keep_last_n is None:
            return []

        # Get all build directories, sorted by modification time
        build_dirs = self._fs.list_directories(self._base_dir, "rebuild-*")
        build_dirs.sort(key=lambda p: p.stat().st_mtime, reverse=True)

        # Delete old ones
        to_delete = build_dirs[self._keep_last_n :]
        deleted = []

        for dir_path in to_delete:
            self._fs.delete_directory(dir_path)
            deleted.append(dir_path)

        return deleted

    async def list_builds(self, limit: int | None = None) -> list[Path]:
        """List recent build directories.

        Args:
            limit: Maximum number to return

        Returns:
            List of build directory paths, newest first
        """
        if not self._base_dir.exists():
            return []

        build_dirs = self._fs.list_directories(self._base_dir, "rebuild-*")
        build_dirs.sort(key=lambda p: p.stat().st_mtime, reverse=True)

        if limit:
            return build_dirs[:limit]
        return build_dirs
