"""NixOS rebuild test runner."""

from __future__ import annotations

import re
from pathlib import Path
from typing import TYPE_CHECKING

from nixos_rebuild_tester.services.interactive_test_runner import InteractiveTestRunner

if TYPE_CHECKING:
    from nixos_rebuild_tester.domain.models import RebuildConfig
    from nixos_rebuild_tester.domain.protocols import TerminalSession


class NixRebuildRunner(InteractiveTestRunner):
    """Run nixos-rebuild tests.

    Specialized runner for NixOS rebuild operations.
    Handles nix-specific command construction and error detection.
    """

    def __init__(
        self,
        session: TerminalSession,
        output_dir: Path,
        config: RebuildConfig,
    ):
        super().__init__(session, output_dir)
        self.config = config
        self._command_sent = False

    async def prepare_test(self) -> None:
        """Prepare rebuild test (no-op for nix rebuilds)."""
        pass

    async def execute_test(self) -> None:
        """Execute nixos-rebuild command."""
        command = self._build_command()
        await self.session.send_command(command)
        self._command_sent = True

    async def is_complete(self) -> bool:
        """Check if rebuild has completed."""
        if not self._command_sent:
            return False

        # Check if command prompt returned
        frame = await self.session.capture_frame()
        return bool(re.search(r'[\$#]\s*$', frame))

    def extract_error(self) -> str | None:
        """Extract error from rebuild output."""
        # Convert frames to strings if needed
        frame_strings = []
        for frame in self.frames:
            if isinstance(frame, str):
                frame_strings.append(frame)
            else:
                # If it's a frame object with content attribute
                frame_strings.append(getattr(frame, 'content', str(frame)))

        for frame in reversed(frame_strings):
            if match := re.search(r'error:.*', frame, re.MULTILINE):
                return match.group(0)
        return None

    def get_timeout(self) -> float:
        return self.config.timeout_seconds

    def get_capture_interval(self) -> float:
        return getattr(self.config, 'capture_interval', 5.0)

    def _build_command(self) -> str:
        """Build nixos-rebuild command."""
        parts = ["sudo", "nixos-rebuild", self.config.action.value]

        if self.config.flake_ref != ".#":
            parts.extend(["--flake", self.config.flake_ref])
        else:
            parts.extend(["--flake", ".#"])

        return " ".join(parts)
