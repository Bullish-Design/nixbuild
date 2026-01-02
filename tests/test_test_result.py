"""Tests for TestResult model and RebuildResult compatibility."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

import pytest

from nixos_rebuild_tester.domain.models import (
    BuildArtifacts,
    RebuildAction,
    RebuildResult,
    TestResult,
)
from nixos_rebuild_tester.domain.value_objects import Duration, Timestamp


def test_test_result_creation():
    """Verify TestResult model creation."""
    now = datetime.now()
    output_dir = Path("/tmp/test")

    result = TestResult(
        success=True,
        exit_code=0,
        timestamp=now,
        duration_seconds=10.5,
        error_message=None,
        output_dir=output_dir,
    )

    assert result.success is True
    assert result.exit_code == 0
    assert result.timestamp == now
    assert result.duration_seconds == 10.5
    assert result.error_message is None
    assert result.output_dir == output_dir
    assert result.metadata == {}


def test_test_result_with_error():
    """Verify TestResult with error."""
    now = datetime.now()
    output_dir = Path("/tmp/test")

    result = TestResult(
        success=False,
        exit_code=1,
        timestamp=now,
        duration_seconds=5.0,
        error_message="Build failed",
        output_dir=output_dir,
    )

    assert result.success is False
    assert result.exit_code == 1
    assert result.error_message == "Build failed"


def test_test_result_with_metadata():
    """Verify TestResult with custom metadata."""
    now = datetime.now()
    output_dir = Path("/tmp/test")

    result = TestResult(
        success=True,
        exit_code=0,
        timestamp=now,
        duration_seconds=10.0,
        output_dir=output_dir,
        metadata={"test_type": "neovim", "config": "default"},
    )

    assert result.metadata["test_type"] == "neovim"
    assert result.metadata["config"] == "default"


def test_rebuild_result_from_test_result():
    """Verify RebuildResult.from_test_result() conversion."""
    now = datetime.now()
    output_dir = Path("/tmp/test")

    # Create a TestResult
    test_result = TestResult(
        success=True,
        exit_code=0,
        timestamp=now,
        duration_seconds=15.5,
        error_message=None,
        output_dir=output_dir,
    )

    # Create BuildArtifacts
    log_file = output_dir / "build.log"
    artifacts = BuildArtifacts(
        log_file=log_file,
        cast_file=None,
        screenshot_file=None,
        gif_file=None,
    )

    # Convert to RebuildResult
    rebuild_result = RebuildResult.from_test_result(
        result=test_result,
        action=RebuildAction.TEST,
        artifacts=artifacts,
    )

    # Verify conversion
    assert rebuild_result.success is True
    assert rebuild_result.exit_code == 0
    assert rebuild_result.timestamp.value == now
    assert rebuild_result.duration.seconds == 15.5
    assert rebuild_result.action == RebuildAction.TEST
    assert rebuild_result.output_dir == output_dir
    assert rebuild_result.artifacts == artifacts
    assert rebuild_result.error_message is None


def test_rebuild_result_from_test_result_with_error():
    """Verify RebuildResult.from_test_result() with error."""
    now = datetime.now()
    output_dir = Path("/tmp/test")

    # Create a failed TestResult
    test_result = TestResult(
        success=False,
        exit_code=1,
        timestamp=now,
        duration_seconds=5.0,
        error_message="error: build failed",
        output_dir=output_dir,
    )

    # Create BuildArtifacts
    log_file = output_dir / "build.log"
    artifacts = BuildArtifacts(log_file=log_file)

    # Convert to RebuildResult
    rebuild_result = RebuildResult.from_test_result(
        result=test_result,
        action=RebuildAction.BUILD,
        artifacts=artifacts,
    )

    # Verify conversion
    assert rebuild_result.success is False
    assert rebuild_result.exit_code == 1
    assert rebuild_result.error_message == "error: build failed"
    assert rebuild_result.action == RebuildAction.BUILD
