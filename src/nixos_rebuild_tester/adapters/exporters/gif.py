"""GIF animation exporter."""

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import TYPE_CHECKING

from terminal_state.export.gif import GifExporter as TSGifExporter

if TYPE_CHECKING:
    from nixos_rebuild_tester.domain.protocols import TerminalSession


class GifExporter:
    """Exports recording as GIF animation."""

    def __init__(self) -> None:
        """Initialize exporter."""
        self._exporter = TSGifExporter()

    async def export(self, session: TerminalSession, output_path: Path) -> Path:
        """Export recording as GIF.

        Args:
            session: Terminal session to export from
            output_path: Path to save GIF

        Returns:
            Path to created GIF file
        """
        recording = getattr(session, "recording", None)
        if recording:
            await asyncio.to_thread(self._exporter.export, recording, output_path)
        return output_path
