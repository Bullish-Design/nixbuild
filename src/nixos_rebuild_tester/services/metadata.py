"""Metadata management service."""

from __future__ import annotations

from pathlib import Path

from nixos_rebuild_tester.domain.models import RebuildResult


class MetadataManager:
    """Manages rebuild result metadata."""

    async def save(self, result: RebuildResult) -> Path:
        """Save result as JSON using Pydantic serialization.

        Args:
            result: Rebuild result to save

        Returns:
            Path to metadata file
        """
        metadata_path = result.metadata_file

        # Use Pydantic's serialization with proper handling
        json_content = result.model_dump_json(indent=2, exclude_none=True)

        metadata_path.write_text(json_content)
        return metadata_path

    async def load(self, metadata_file: Path) -> RebuildResult:
        """Load result from metadata file.

        Args:
            metadata_file: Path to metadata JSON file

        Returns:
            Loaded rebuild result

        Raises:
            FileNotFoundError: If metadata file doesn't exist
            ValueError: If metadata file is invalid
        """
        if not metadata_file.exists():
            raise FileNotFoundError(f"Metadata file not found: {metadata_file}")

        json_content = metadata_file.read_text()
        return RebuildResult.model_validate_json(json_content)
