"""Coordinates artifact export with parallel execution."""

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from nixos_rebuild_tester.domain.protocols import ArtifactExporter, ArtifactReference
    from nixos_rebuild_tester.domain.value_objects import BuildId, OutputDirectory


class ExportPipeline:
    """Coordinates export of build artifacts.

    Manages parallel execution of multiple exporters to generate
    all configured artifact types.
    """

    def __init__(self, exporters: list[ArtifactExporter]):
        """Initialize export pipeline.

        Args:
            exporters: List of exporters to run
        """
        self._exporters = exporters

    async def export_all(
        self,
        frames: list[str],
        output_dir: OutputDirectory,
        build_id: BuildId,
    ) -> list[ArtifactReference]:
        """Export all artifacts in parallel.

        Args:
            frames: Terminal frames to export
            output_dir: Output directory
            build_id: Build identifier for metadata

        Returns:
            List of artifact references
        """
        # Create export metadata
        metadata = _ExportMetadata(build_id)

        # Create export tasks for all exporters
        export_tasks = []
        for exporter in self._exporters:
            # Determine output path based on exporter type
            output_path = self._get_output_path(exporter, output_dir)
            task = exporter.export(frames, output_path, metadata)
            export_tasks.append(task)

        # Run all exports concurrently
        try:
            artifacts = await asyncio.gather(*export_tasks, return_exceptions=True)
        except Exception:
            # If any export fails, still return successful ones
            artifacts = []

        # Filter out exceptions and return successful artifacts
        return [art for art in artifacts if not isinstance(art, Exception)]

    def _get_output_path(
        self,
        exporter: ArtifactExporter,
        output_dir: OutputDirectory,
    ) -> Path:
        """Determine output path for exporter.

        Args:
            exporter: Exporter instance
            output_dir: Output directory

        Returns:
            Path for this exporter's output
        """
        # Map exporter types to paths
        # This is a simplified version - real implementation would be more robust
        exporter_name = exporter.__class__.__name__.lower()

        if "log" in exporter_name:
            return output_dir.log_file
        elif "asciinema" in exporter_name or "cast" in exporter_name:
            return output_dir.cast_file
        elif "screenshot" in exporter_name:
            return output_dir.screenshot_file
        elif "gif" in exporter_name:
            return output_dir.gif_file
        else:
            return output_dir.path / f"artifact-{exporter_name}"


class _ExportMetadata:
    """Simple export metadata implementation."""

    def __init__(self, build_id: BuildId):
        """Initialize metadata.

        Args:
            build_id: Build identifier
        """
        self._build_id = build_id

    @property
    def timestamp(self) -> str:
        """Export timestamp."""
        return self._build_id.timestamp.iso_format

    @property
    def build_id(self) -> BuildId:
        """Build identifier."""
        return self._build_id
