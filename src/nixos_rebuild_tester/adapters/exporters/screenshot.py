"""Screenshot exporter - exports final frame as PNG."""

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import TYPE_CHECKING

from terminal_state.export.screenshot import ScreenshotExporter as TSScreenshotExporter

if TYPE_CHECKING:
    from nixos_rebuild_tester.domain.protocols import TerminalSession


class ScreenshotExporter:
    """Exports final frame as PNG screenshot."""

    def __init__(self) -> None:
        """Initialize exporter."""
        self._exporter = TSScreenshotExporter()

    async def export(self, session: TerminalSession, output_path: Path) -> Path:
        """Export final frame screenshot.

        Args:
            session: Terminal session to export from
            output_path: Path to save screenshot

        Returns:
            Path to created screenshot file
        """
        recording = getattr(session, "recording", None)
        if recording and recording.frames:
            final_frame = recording.frames[-1]
            await asyncio.to_thread(self._exporter.export_frame, final_frame, output_path)
        return output_path
