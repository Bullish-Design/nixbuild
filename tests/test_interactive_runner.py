"""Tests for generic interactive test runner."""

from __future__ import annotations

import asyncio
from datetime import datetime
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest

from nixos_rebuild_tester.domain.models import TestResult
from nixos_rebuild_tester.services.interactive_test_runner import InteractiveTestRunner


class DummyRunner(InteractiveTestRunner):
    """Test implementation of InteractiveTestRunner."""

    def __init__(self, session, output_dir, should_fail=False):
        super().__init__(session, output_dir)
        self.should_fail = should_fail
        self.test_executed = False

    async def prepare_test(self) -> None:
        """Prepare test (no-op)."""
        pass

    async def execute_test(self) -> None:
        """Execute test."""
        self.test_executed = True
        await asyncio.sleep(0.1)  # Simulate work

    async def is_complete(self) -> bool:
        """Check if test completed."""
        return self.test_executed

    def extract_error(self) -> str | None:
        """Extract error."""
        if self.should_fail:
            return "Test failed"
        return None

    def get_timeout(self) -> float:
        """Get timeout."""
        return 10.0

    def get_capture_interval(self) -> float:
        """Get capture interval."""
        return 0.1


@pytest.fixture
def mock_session():
    """Create mock terminal session."""
    session = MagicMock()
    session.capture = MagicMock(return_value="test frame")
    session.capture_frame = AsyncMock(return_value="test frame")
    session.send_command = AsyncMock()
    return session


@pytest.fixture
def output_dir(tmp_path):
    """Create temporary output directory."""
    return tmp_path / "test_output"


@pytest.mark.asyncio
async def test_runner_success_lifecycle(mock_session, output_dir):
    """Verify runner completes successful test lifecycle."""
    runner = DummyRunner(mock_session, output_dir, should_fail=False)
    result = await runner.run()

    assert isinstance(result, TestResult)
    assert result.success is True
    assert result.exit_code == 0
    assert result.error_message is None
    assert result.duration_seconds > 0
    assert isinstance(result.timestamp, datetime)
    assert result.output_dir == output_dir


@pytest.mark.asyncio
async def test_runner_failure_lifecycle(mock_session, output_dir):
    """Verify runner handles test failure."""
    runner = DummyRunner(mock_session, output_dir, should_fail=True)
    result = await runner.run()

    assert isinstance(result, TestResult)
    assert result.success is False
    assert result.exit_code == 1
    assert result.error_message == "Test failed"
    assert result.duration_seconds > 0


@pytest.mark.asyncio
async def test_runner_captures_frames(mock_session, output_dir):
    """Verify runner captures frames during execution."""
    runner = DummyRunner(mock_session, output_dir)
    await runner.run()

    # Should have captured at least one frame
    assert len(runner.frames) > 0


@pytest.mark.asyncio
async def test_runner_timeout_handling(mock_session, output_dir):
    """Verify runner handles timeout."""

    class TimeoutRunner(DummyRunner):
        async def is_complete(self) -> bool:
            # Never completes
            return False

        def get_timeout(self) -> float:
            return 0.2  # Very short timeout

    runner = TimeoutRunner(mock_session, output_dir)
    result = await runner.run()

    # Should fail with timeout error
    assert result.success is False
    assert "timeout" in result.error_message.lower()
