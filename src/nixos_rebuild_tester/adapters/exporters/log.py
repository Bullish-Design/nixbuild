"""Log file exporter - exports terminal frames as text."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from nixos_rebuild_tester.domain.protocols import ITerminalSession


class LogExporter:
    """Exports all frames as plain text log."""

    async def export(self, session: ITerminalSession, output_path: Path) -> Path:
        """Export frames as text log.

        Args:
            session: Terminal session to export from
            output_path: Path to save log file

        Returns:
            Path to created log file
        """
        separator = "=" * 80

        with output_path.open("w") as f:
            for frame in session.frames:
                f.write(frame)
                f.write(f"\n{separator}\n")

        return output_path
