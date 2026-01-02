"""Log file exporter - exports terminal frames as text."""

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from nixos_rebuild_tester.domain.protocols import TerminalSession


def _write_log(frames: list[str], output_path: Path) -> None:
    """Write frames to log file (synchronous helper).

    Args:
        frames: List of frame content strings
        output_path: Path to save log file
    """
    separator = "=" * 80

    with output_path.open("w") as f:
        for frame in frames:
            f.write(frame)
            f.write(f"\n{separator}\n")


class LogExporter:
    """Exports all frames as plain text log."""

    async def export(self, session: TerminalSession, output_path: Path) -> Path:
        """Export frames as text log.

        Args:
            session: Terminal session to export from
            output_path: Path to save log file

        Returns:
            Path to created log file
        """
        await asyncio.to_thread(_write_log, session.frames, output_path)
        return output_path
