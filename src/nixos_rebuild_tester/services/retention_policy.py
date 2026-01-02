"""Determines which builds to keep or delete."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from nixos_rebuild_tester.domain.models import RebuildResult
    from nixos_rebuild_tester.domain.value_objects import BuildId


class RetentionPolicy:
    """Determines which builds to keep/delete.

    Implements retention logic to manage build history size.
    """

    def __init__(self, keep_last_n: int | None = None):
        """Initialize retention policy.

        Args:
            keep_last_n: Number of builds to keep (None = keep all)
        """
        self._keep_last_n = keep_last_n

    def select_for_deletion(
        self,
        builds: list[RebuildResult],
        keep_last_n: int | None = None,
    ) -> list[BuildId]:
        """Select builds for deletion based on policy.

        Args:
            builds: List of build results (should be sorted by timestamp, newest first)
            keep_last_n: Optional override for keep count

        Returns:
            List of BuildIds to delete
        """
        keep_count = keep_last_n if keep_last_n is not None else self._keep_last_n

        # If no retention limit, don't delete anything
        if keep_count is None:
            return []

        # Sort builds by timestamp (newest first)
        sorted_builds = sorted(
            builds,
            key=lambda b: b.timestamp.value,
            reverse=True,
        )

        # Select builds beyond retention limit
        to_delete = sorted_builds[keep_count:]

        # Return BuildIds for deletion
        # Note: We'll need to add build_id to RebuildResult or extract from output_dir
        return [self._extract_build_id(build) for build in to_delete]

    def _extract_build_id(self, result: RebuildResult) -> BuildId:
        """Extract BuildId from RebuildResult.

        Temporary method until RebuildResult includes BuildId.

        Args:
            result: Rebuild result

        Returns:
            BuildId
        """
        from nixos_rebuild_tester.domain.value_objects import BuildId

        # For now, create a BuildId from the timestamp
        return BuildId(timestamp=result.timestamp, sequence=0)
