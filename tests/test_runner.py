"""Tests for rebuild application and services."""

from __future__ import annotations

from pathlib import Path

import pytest

from nixos_rebuild_tester.adapters.filesystem import LocalFileSystem
from nixos_rebuild_tester.domain.models import Config, OutputConfig, RebuildAction
from nixos_rebuild_tester.services.executor import BuildExecutor, ExecutionConfig
from nixos_rebuild_tester.services.history import BuildHistoryManager


def test_create_output_dir(tmp_path):
    """Verify output directory creation."""
    filesystem = LocalFileSystem()
    manager = BuildHistoryManager(filesystem, tmp_path, keep_last_n=None)

    output_dir = manager.create_build_directory()

    assert output_dir.exists()
    assert output_dir.is_dir()
    assert output_dir.name.startswith("rebuild-")


@pytest.mark.asyncio
async def test_cleanup_old_builds(tmp_path):
    """Verify old build deletion."""
    # Create 5 fake build directories
    for i in range(5):
        (tmp_path / f"rebuild-{i:03d}").mkdir()

    filesystem = LocalFileSystem()
    manager = BuildHistoryManager(filesystem, tmp_path, keep_last_n=3)

    deleted = await manager.cleanup_old_builds()

    # Should have deleted 2 directories
    assert len(deleted) == 2

    # Should have only 3 directories left
    remaining = list(tmp_path.glob("rebuild-*"))
    assert len(remaining) == 3


def test_extract_error_from_frames():
    """Verify error extraction."""
    exec_config = ExecutionConfig(
        action=RebuildAction.TEST,
        flake_ref=".#",
        timeout_seconds=1800,
    )
    executor = BuildExecutor(exec_config)

    content = """
    building
    some output
    error: builder for '/nix/store/xxx' failed with exit code 1
    more output
    """

    error = executor._extract_error_from_frames([content])
    assert "error:" in error
    assert "failed" in error
