"""Coordinates artifact export with parallel execution."""

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from nixos_rebuild_tester.domain.protocols import ArtifactExporter, TerminalSession
    from nixos_rebuild_tester.domain.value_objects import OutputDirectory


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
        session: TerminalSession,
        output_dir: OutputDirectory,
    ) -> list[Path]:
        """Export all artifacts in parallel.

        Args:
            session: Terminal session to export
            output_dir: Output directory

        Returns:
            List of exported artifact paths
        """
        # Create export tasks for all exporters
        export_tasks = []
        for exporter in self._exporters:
            # Determine output path based on exporter type
            output_path = self._get_output_path(exporter, output_dir)
            task = exporter.export(session, output_path)
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

