"""Factory for creating exporters based on configuration."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from nixos_rebuild_tester.domain.models import RecordingConfig
    from nixos_rebuild_tester.domain.protocols import ArtifactExporter


class ExporterRegistry:
    """Factory for creating exporters based on configuration.

    This registry creates and configures the appropriate exporters
    based on the recording configuration.
    """

    def create_exporters(self, config: RecordingConfig) -> list[ArtifactExporter]:
        """Create list of exporters based on config.

        Args:
            config: Recording configuration

        Returns:
            List of configured exporters
        """
        from nixos_rebuild_tester.adapters.exporters.asciinema import AsciinemaExporter
        from nixos_rebuild_tester.adapters.exporters.gif import GifExporter
        from nixos_rebuild_tester.adapters.exporters.log import LogExporter
        from nixos_rebuild_tester.adapters.exporters.screenshot import ScreenshotExporter

        exporters: list[ArtifactExporter] = []

        # Log exporter (always enabled)
        exporters.append(LogExporter())

        # Conditional exporters based on config
        if config.enabled:
            exporters.append(AsciinemaExporter())

            if config.export_screenshot:
                exporters.append(ScreenshotExporter())

            if config.export_gif:
                exporters.append(GifExporter())

        return exporters
