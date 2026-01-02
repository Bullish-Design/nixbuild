"""Removes old build data based on retention policy."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from nixos_rebuild_tester.domain.protocols import FileSystem


class BuildCleaner:
    """Removes old build data.

    Deletes build directories based on retention policy.
    """

    def __init__(
        self,
        filesystem: FileSystem,
        base_directory: Path,
        keep_last_n: int | None,
    ):
        """Initialize build cleaner.

        Args:
            filesystem: Filesystem implementation
            base_directory: Base directory containing rebuild outputs
            keep_last_n: Number of builds to keep (None = keep all)
        """
        self._filesystem = filesystem
        self._base_dir = base_directory.expanduser().absolute()
        self._keep_last_n = keep_last_n

    async def cleanup(self, keep_last_n: int | None = None) -> list[Path]:
        """Clean up old builds based on policy.

        Args:
            keep_last_n: Optional override for retention count

        Returns:
            List of deleted build directories
        """
        keep_count = keep_last_n if keep_last_n is not None else self._keep_last_n
        if keep_count is None:
            return []

        rebuild_dirs = self._filesystem.list_directories(self._base_dir, "rebuild-*")
        if not rebuild_dirs:
            return []

        sorted_dirs = sorted(
            rebuild_dirs,
            key=lambda path: (self._filesystem.get_modified_time(path), path.name),
            reverse=True,
        )

        to_delete = sorted_dirs[keep_count:]
        deleted: list[Path] = []
        for directory in to_delete:
            try:
                self._filesystem.delete_directory(directory)
                deleted.append(directory)
            except Exception:
                continue

        return deleted
