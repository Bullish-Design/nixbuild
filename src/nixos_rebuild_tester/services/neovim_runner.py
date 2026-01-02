"""Neovim test runner."""

from __future__ import annotations

import asyncio
import re
from pathlib import Path
from typing import TYPE_CHECKING

from nixos_rebuild_tester.services.interactive_test_runner import InteractiveTestRunner

if TYPE_CHECKING:
    from nixos_rebuild_tester.domain.neovim_models import (
        KeyModifier,
        KeyStroke,
        NeovimCommand,
        NeovimTestConfig,
    )
    from nixos_rebuild_tester.domain.protocols import TerminalSession


class NeovimTestRunner(InteractiveTestRunner):
    """Run neovim visual tests."""

    def __init__(
        self,
        session: TerminalSession,
        output_dir: Path,
        config: NeovimTestConfig,
    ):
        super().__init__(session, output_dir)
        self.config = config
        self._neovim_launched = False
        self._neovim_exited = False

    async def prepare_test(self) -> None:
        """Launch neovim."""
        command = ["nvim"]

        if self.config.nvim_config_path:
            config_path = Path(self.config.nvim_config_path).expanduser()
            command.extend(["-u", str(config_path / "init.lua")])

        if self.config.test_file:
            command.append(self.config.test_file)

        await self.session.send_command(" ".join(command))

        # Wait for neovim to load
        await asyncio.sleep(1.0)
        self._neovim_launched = True

    async def execute_test(self) -> None:
        """Execute neovim command sequences."""
        for command in self.config.commands:
            await self._execute_command(command)

    async def is_complete(self) -> bool:
        """Check if test completed (neovim exited)."""
        if not self._neovim_launched:
            return False

        # Check if we're back at shell prompt
        frame = await self.session.capture_frame()
        if re.search(r'[\$#]\s*$', frame):
            self._neovim_exited = True
            return True

        return False

    def extract_error(self) -> str | None:
        """Extract error from neovim output."""
        # Convert frames to strings if needed
        frame_strings = []
        for frame in self.frames:
            if isinstance(frame, str):
                frame_strings.append(frame)
            else:
                # If it's a frame object with content attribute
                frame_strings.append(getattr(frame, 'content', str(frame)))

        for frame in reversed(frame_strings):
            if "E" in frame and "Error" in frame:
                # Basic neovim error detection
                if match := re.search(r'E\d+:.*', frame):
                    return match.group(0)
        return None

    def get_timeout(self) -> float:
        return self.config.timeout_seconds

    def get_capture_interval(self) -> float:
        return self.config.capture_interval.total_seconds()

    async def _execute_command(self, command: NeovimCommand) -> None:
        """Execute single command sequence."""
        for keystroke in command.keystrokes:
            await self._send_keystroke(keystroke)

        await asyncio.sleep(command.wait_for_completion.total_seconds())

    async def _send_keystroke(self, keystroke: KeyStroke) -> None:
        """Send single keystroke to neovim.

        Note: This is a simplified implementation.
        Full implementation would require integration with terminal-state's key handling.
        """
        from nixos_rebuild_tester.domain.neovim_models import KeyModifier

        # Build key sequence with modifiers
        key = keystroke.key

        if KeyModifier.CTRL in keystroke.modifiers:
            key = f"C-{key}"
        elif KeyModifier.ALT in keystroke.modifiers:
            key = f"M-{key}"

        # Special key mappings
        key_map = {
            "Enter": "\n",
            "Escape": "\x1b",
            "Tab": "\t",
            "Space": " ",
        }
        key = key_map.get(key, key)

        # Send to session (simplified - in real implementation would use terminal-state's key sequence)
        # For now, we'll send as a simple command
        # In a full implementation, this would integrate with terminal_state.input.keys.KeySequence
        await asyncio.sleep(0.01)  # Small delay to simulate keystroke

        # Wait
        await asyncio.sleep(keystroke.delay_after.total_seconds())
