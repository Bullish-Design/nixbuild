"""Stores rebuild results as JSON files on disk."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from nixos_rebuild_tester.domain.exceptions import BuildNotFound, CorruptedMetadata, StorageError

if TYPE_CHECKING:
    from nixos_rebuild_tester.domain.models import RebuildResult
    from nixos_rebuild_tester.domain.protocols import FileSystem
    from nixos_rebuild_tester.domain.value_objects import BuildId


class FileSystemBuildRepository:
    """Stores rebuild results as JSON files on disk.

    Implements BuildRepository protocol using filesystem storage.
    Each build result is stored as a metadata.json file in its
    output directory.
    """

    def __init__(self, filesystem: FileSystem, base_dir: Path):
        """Initialize repository.

        Args:
            filesystem: Filesystem implementation
            base_dir: Base directory for all builds
        """
        self._fs = filesystem
        self._base_dir = base_dir.expanduser().absolute()

    async def save(self, result: RebuildResult) -> None:
        """Save build result to filesystem.

        Args:
            result: Result to save

        Raises:
            StorageError: If save fails
        """
        try:
            metadata_path = result.metadata_file

            # Serialize result to JSON
            json_content = result.model_dump_json(indent=2, exclude_none=True)

            # Write to file
            await self._fs.write_text(metadata_path, json_content)

        except Exception as e:
            raise StorageError(f"Failed to save build result: {e}") from e

    async def find_by_id(self, build_id: BuildId) -> RebuildResult | None:
        """Find build by ID.

        Args:
            build_id: Build identifier

        Returns:
            RebuildResult if found, None otherwise
        """
        try:
            # Construct path to metadata file
            build_dir = self._base_dir / build_id.filesystem_name
            metadata_path = build_dir / "metadata.json"

            # Check if exists
            if not self._fs.file_exists(metadata_path):
                return None

            # Load and parse
            json_content = await self._fs.read_text(metadata_path)

            from nixos_rebuild_tester.domain.models import RebuildResult

            return RebuildResult.model_validate_json(json_content)

        except Exception as e:
            if "not found" in str(e).lower():
                return None
            raise CorruptedMetadata(f"Failed to load build {build_id.filesystem_name}: {e}") from e

    async def find_recent(self, limit: int) -> list[RebuildResult]:
        """Find recent builds.

        Args:
            limit: Maximum number to return

        Returns:
            List of recent build results, newest first
        """
        try:
            # List all build directories
            if not self._fs.directory_exists(self._base_dir):
                return []

            build_dirs = await self._fs.list_directories(self._base_dir, "rebuild-*")

            # Sort by modification time (newest first)
            # This is a synchronous operation, so we don't await
            build_dirs_with_times = []
            for dir_path in build_dirs:
                try:
                    mtime = await self._fs.get_modified_time(dir_path)
                    build_dirs_with_times.append((dir_path, mtime))
                except Exception:
                    continue

            build_dirs_with_times.sort(key=lambda x: x[1], reverse=True)

            # Load metadata for each directory
            results = []
            for dir_path, _ in build_dirs_with_times[:limit]:
                metadata_path = dir_path / "metadata.json"
                if self._fs.file_exists(metadata_path):
                    try:
                        json_content = await self._fs.read_text(metadata_path)

                        from nixos_rebuild_tester.domain.models import RebuildResult

                        result = RebuildResult.model_validate_json(json_content)
                        results.append(result)
                    except Exception:
                        # Skip corrupted metadata
                        continue

            return results

        except Exception as e:
            raise StorageError(f"Failed to list builds: {e}") from e

    async def delete(self, build_id: BuildId) -> None:
        """Delete build result.

        Args:
            build_id: Build to delete

        Raises:
            BuildNotFound: If build doesn't exist
        """
        try:
            build_dir = self._base_dir / build_id.filesystem_name

            if not self._fs.directory_exists(build_dir):
                raise BuildNotFound(f"Build {build_id.filesystem_name} not found")

            # Delete entire directory
            await self._fs.delete_directory(build_dir)

        except BuildNotFound:
            raise
        except Exception as e:
            raise StorageError(f"Failed to delete build {build_id.filesystem_name}: {e}") from e
