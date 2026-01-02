"""Tests for data models."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from nixos_rebuild_tester.models import Config, RebuildAction, RebuildConfig, RecordingConfig


def test_config_defaults():
    """Verify default configuration values."""
    config = Config()
    assert config.recording.enabled is True
    assert config.recording.width == 120
    assert config.rebuild.action == RebuildAction.TEST
    assert config.output.keep_last_n is None


def test_recording_config_validation():
    """Verify recording config validation."""
    # Valid
    RecordingConfig(width=100, height=30)

    # Invalid width
    with pytest.raises(ValidationError):
        RecordingConfig(width=300)  # > 200

    # Invalid height
    with pytest.raises(ValidationError):
        RecordingConfig(height=10)  # < 20


def test_rebuild_action_enum():
    """Verify RebuildAction enum values."""
    assert RebuildAction.TEST.value == "test"
    assert RebuildAction.BUILD.value == "build"
    assert RebuildAction.DRY_BUILD.value == "dry-build"


def test_rebuild_config_defaults():
    """Verify rebuild config defaults."""
    config = RebuildConfig()
    assert config.action == RebuildAction.TEST
    assert config.flake_ref == ".#"
    assert config.timeout_seconds == 1800


def test_config_override():
    """Verify partial config override."""
    config = Config(rebuild=RebuildConfig(action=RebuildAction.BUILD))
    assert config.rebuild.action == RebuildAction.BUILD
    assert config.recording.enabled is True  # Still default
