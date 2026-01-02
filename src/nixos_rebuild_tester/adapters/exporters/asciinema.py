"""Asciinema cast file exporter."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from terminal_state.export.asciinema import AsciinemaExporter as TSAsciinemaExporter

if TYPE_CHECKING:
    from nixos_rebuild_tester.adapters.terminal import TmuxTerminalAdapter


class AsciinemaExporter:
    """Exports recording in asciinema format."""

    def __init__(self) -> None:
        """Initialize exporter."""
        self._exporter = TSAsciinemaExporter()

    async def export(self, session: TmuxTerminalAdapter, output_path: Path) -> Path:
        """Export asciinema cast file.

        Args:
            session: Terminal session to export from
            output_path: Path to save cast file

        Returns:
            Path to created cast file
        """
        if session.recording:
            self._exporter.export(session.recording, output_path)
        return output_path
