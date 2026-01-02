"""Artifact export coordination service."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

from nixos_rebuild_tester.domain.models import BuildArtifacts

if TYPE_CHECKING:
    from nixos_rebuild_tester.domain.protocols import IArtifactExporter, ITerminalSession


@dataclass(frozen=True)
class ExportConfig:
    """Configuration for artifact export."""

    export_cast: bool = True
    export_screenshot: bool = True
    export_gif: bool = False
    export_log: bool = True


class ArtifactExportService:
    """Coordinates export of build artifacts."""

    def __init__(
        self,
        exporters: dict[str, IArtifactExporter],
        config: ExportConfig,
    ):
        """Initialize export service.

        Args:
            exporters: Dictionary of exporter name to exporter instance
            config: Export configuration
        """
        self._exporters = exporters
        self._config = config

    async def export_all(
        self,
        session: ITerminalSession,
        output_dir: Path,
    ) -> BuildArtifacts:
        """Export all configured artifacts.

        Args:
            session: Terminal session to export from
            output_dir: Directory to save artifacts

        Returns:
            BuildArtifacts with paths to created files
        """
        files: dict[str, Path | None] = {}

        # Log file (always required)
        if self._config.export_log and "log" in self._exporters:
            files["log_file"] = await self._exporters["log"].export(session, output_dir / "rebuild.log")
        else:
            # Create empty log file as fallback
            log_file = output_dir / "rebuild.log"
            log_file.touch()
            files["log_file"] = log_file

        # Cast file (optional)
        if self._config.export_cast and "cast" in self._exporters:
            files["cast_file"] = await self._exporters["cast"].export(session, output_dir / "rebuild.cast")
        else:
            files["cast_file"] = None

        # Screenshot (optional)
        if self._config.export_screenshot and "screenshot" in self._exporters:
            files["screenshot_file"] = await self._exporters["screenshot"].export(session, output_dir / "final.png")
        else:
            files["screenshot_file"] = None

        # GIF (optional)
        if self._config.export_gif and "gif" in self._exporters:
            files["gif_file"] = await self._exporters["gif"].export(session, output_dir / "rebuild.gif")
        else:
            files["gif_file"] = None

        return BuildArtifacts(**files)  # type: ignore
