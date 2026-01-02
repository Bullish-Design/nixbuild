"""Creates and manages build output directories."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from nixos_rebuild_tester.domain.exceptions import DirectoryCreationFailed
from nixos_rebuild_tester.domain.value_objects import BuildId, OutputDirectory

if TYPE_CHECKING:
    from nixos_rebuild_tester.domain.protocols import FileSystem


class BuildDirectoryManager:
    """Creates and manages build output directories.

    Handles creation of build-specific output directories with
    proper naming and structure.
    """

    def __init__(self, filesystem: FileSystem, base_directory: Path):
        """Initialize directory manager.

        Args:
            filesystem: Filesystem implementation
            base_directory: Base directory for all builds
        """
        self._fs = filesystem
        self._base_dir = base_directory.expanduser().absolute()

    async def create_for_build(self, build_id: BuildId) -> OutputDirectory:
        """Create output directory for build.

        Args:
            build_id: Build identifier

        Returns:
            OutputDirectory with all paths

        Raises:
            DirectoryCreationFailed: If creation fails
        """
        try:
            # Ensure base directory exists
            await self.ensure_base_directory()

            # Create build-specific directory
            dir_path = self._base_dir / build_id.filesystem_name
            created_path = await self._fs.create_directory(dir_path)

            return OutputDirectory(
                path=created_path,
                build_id=build_id,
            )

        except Exception as e:
            raise DirectoryCreationFailed(
                f"Failed to create directory for build {build_id.filesystem_name}: {e}"
            ) from e

    async def ensure_base_directory(self) -> Path:
        """Ensure base directory exists.

        Returns:
            Base directory path

        Raises:
            DirectoryCreationFailed: If creation fails
        """
        try:
            return await self._fs.create_directory(self._base_dir)
        except Exception as e:
            raise DirectoryCreationFailed(f"Failed to create base directory {self._base_dir}: {e}") from e

    def get_base_directory(self) -> Path:
        """Get base directory path.

        Returns:
            Base directory path
        """
        return self._base_dir
