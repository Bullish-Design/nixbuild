"""Base class for interactive command testing."""

from __future__ import annotations

import asyncio
from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING

from nixos_rebuild_tester.domain.models import TestResult
from nixos_rebuild_tester.domain.protocols import TerminalSession

if TYPE_CHECKING:
    from nixos_rebuild_tester.capture.frame import Frame


class InteractiveTestRunner(ABC):
    """Base class for running and recording interactive tests.

    Provides common infrastructure for:
    - Session management
    - Frame recording
    - Error detection
    - Result generation

    Subclasses implement test-specific logic:
    - Command construction
    - Completion detection
    - Error parsing
    """

    def __init__(self, session: TerminalSession, output_dir: Path):
        self.session = session
        self.output_dir = output_dir
        self.frames: list[Frame] = []
        self.start_time: datetime | None = None
        self.end_time: datetime | None = None

    @abstractmethod
    async def prepare_test(self) -> None:
        """Prepare test environment (launch apps, set state, etc)."""
        pass

    @abstractmethod
    async def execute_test(self) -> None:
        """Execute the test sequence."""
        pass

    @abstractmethod
    async def is_complete(self) -> bool:
        """Check if test has completed."""
        pass

    @abstractmethod
    def extract_error(self) -> str | None:
        """Extract error message from frames if test failed."""
        pass

    async def run(self) -> TestResult:
        """Run complete test lifecycle."""
        self.start_time = datetime.now()

        try:
            await self.prepare_test()

            # Start frame recording
            recording_task = asyncio.create_task(self._record_frames())

            await self.execute_test()

            # Wait for completion
            await self._wait_for_completion(timeout=self.get_timeout())

            # Stop recording
            recording_task.cancel()
            try:
                await recording_task
            except asyncio.CancelledError:
                pass

            self.end_time = datetime.now()

            return self._build_result()

        except Exception as e:
            self.end_time = datetime.now()
            return self._build_error_result(e)

    async def _record_frames(self) -> None:
        """Record frames at configured interval."""
        while True:
            frame = self.session.capture()
            self.frames.append(frame)
            await asyncio.sleep(self.get_capture_interval())

    async def _wait_for_completion(self, timeout: float) -> None:
        """Wait for test completion or timeout."""
        start = asyncio.get_event_loop().time()
        while asyncio.get_event_loop().time() - start < timeout:
            if await self.is_complete():
                return
            await asyncio.sleep(0.5)
        raise TimeoutError(f"Test did not complete within {timeout}s")

    def _build_result(self) -> TestResult:
        """Build successful test result."""
        duration = (self.end_time - self.start_time).total_seconds()
        error = self.extract_error()

        return TestResult(
            success=error is None,
            exit_code=0 if error is None else 1,
            timestamp=self.start_time,
            duration_seconds=duration,
            error_message=error,
            output_dir=self.output_dir,
        )

    def _build_error_result(self, exception: Exception) -> TestResult:
        """Build error test result."""
        duration = (self.end_time - self.start_time).total_seconds()

        return TestResult(
            success=False,
            exit_code=1,
            timestamp=self.start_time,
            duration_seconds=duration,
            error_message=str(exception),
            output_dir=self.output_dir,
        )

    @abstractmethod
    def get_timeout(self) -> float:
        """Get test timeout in seconds."""
        pass

    @abstractmethod
    def get_capture_interval(self) -> float:
        """Get frame capture interval in seconds."""
        pass
