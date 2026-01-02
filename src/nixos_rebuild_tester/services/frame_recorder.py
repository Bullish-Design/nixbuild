"""Records terminal frames during execution."""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from nixos_rebuild_tester.domain.protocols import TerminalSession


class FrameRecorder:
    """Records terminal frames during command execution.

    Captures terminal state at regular intervals to create
    a recording of the rebuild process.
    """

    async def record(
        self,
        session: TerminalSession,
        interval_seconds: float = 5.0,
        max_frames: int = 1000,
    ) -> list[str]:
        """Record frames from terminal session.

        Captures frames at regular intervals until session completes
        or max_frames is reached.

        Args:
            session: Terminal session to record
            interval_seconds: Seconds between frame captures
            max_frames: Maximum number of frames to capture

        Returns:
            List of captured frame contents
        """
        frames = []

        try:
            while len(frames) < max_frames:
                # Capture current frame
                frame = await session.capture_frame()
                frames.append(frame)

                # Wait for next interval
                await asyncio.sleep(interval_seconds)

        except asyncio.CancelledError:
            # Recording was cancelled (normal termination)
            pass

        return frames
