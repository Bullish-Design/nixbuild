"""Removes old build data based on retention policy."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from nixos_rebuild_tester.domain.protocols import BuildRepository, FileSystem
    from nixos_rebuild_tester.domain.value_objects import BuildId
    from nixos_rebuild_tester.services.storage.retention_policy import RetentionPolicy


class BuildCleaner:
    """Removes old build data.

    Deletes build directories and metadata based on retention policy.
    """

    def __init__(
        self,
        repository: BuildRepository,
        filesystem: FileSystem,
        policy: RetentionPolicy,
    ):
        """Initialize build cleaner.

        Args:
            repository: Build repository
            filesystem: Filesystem implementation
            policy: Retention policy
        """
        self._repository = repository
        self._filesystem = filesystem
        self._policy = policy

    async def cleanup(self, keep_last_n: int | None = None) -> list[BuildId]:
        """Clean up old builds based on policy.

        Args:
            keep_last_n: Optional override for retention count

        Returns:
            List of deleted BuildIds
        """
        # Get all builds from repository
        all_builds = await self._repository.find_recent(limit=10000)  # Large limit

        # Determine which to delete
        to_delete = self._policy.select_for_deletion(all_builds, keep_last_n)

        # Delete each build
        deleted = []
        for build_id in to_delete:
            try:
                await self._repository.delete(build_id)
                deleted.append(build_id)
            except Exception:
                # Log error but continue with other deletions
                continue

        return deleted
