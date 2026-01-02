"""Tests for rebuild runner."""

from __future__ import annotations

from pathlib import Path

import pytest

from nixos_rebuild_tester.models import Config, OutputConfig
from nixos_rebuild_tester.runner import RebuildRunner


def test_create_output_dir(tmp_path):
    """Verify output directory creation."""
    config = Config(output=OutputConfig(base_dir=tmp_path))
    runner = RebuildRunner(config)

    output_dir = runner._create_output_dir()

    assert output_dir.exists()
    assert output_dir.is_dir()
    assert output_dir.name.startswith("rebuild-")


def test_cleanup_old_builds(tmp_path):
    """Verify old build deletion."""
    # Create 5 fake build directories
    for i in range(5):
        (tmp_path / f"rebuild-{i:03d}").mkdir()

    config = Config(output=OutputConfig(base_dir=tmp_path, keep_last_n=3))
    runner = RebuildRunner(config)

    runner._cleanup_old_builds()

    # Should have only 3 directories left
    remaining = list(tmp_path.glob("rebuild-*"))
    assert len(remaining) == 3


def test_extract_error_from_frame():
    """Verify error extraction."""
    runner = RebuildRunner(Config())

    content = """
    building
    some output
    error: builder for '/nix/store/xxx' failed with exit code 1
    more output
    """

    error = runner._extract_error_from_frame(content)
    assert "error:" in error
    assert "failed" in error
