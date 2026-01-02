"""Tests for neovim models."""

from __future__ import annotations

from datetime import timedelta

import pytest
from pydantic import ValidationError

from nixos_rebuild_tester.domain.neovim_models import (
    KeyModifier,
    KeyStroke,
    NeovimCommand,
    NeovimTestConfig,
)


def test_key_modifier_enum():
    """Verify KeyModifier enum values."""
    assert KeyModifier.CTRL.value == "ctrl"
    assert KeyModifier.ALT.value == "alt"
    assert KeyModifier.SHIFT.value == "shift"


def test_keystroke_creation():
    """Verify KeyStroke model creation."""
    keystroke = KeyStroke(key="i")
    assert keystroke.key == "i"
    assert keystroke.modifiers == []
    assert keystroke.delay_after == timedelta(milliseconds=100)


def test_keystroke_with_modifiers():
    """Verify KeyStroke with modifiers."""
    keystroke = KeyStroke(
        key="c",
        modifiers=[KeyModifier.CTRL],
        delay_after=timedelta(milliseconds=200),
    )
    assert keystroke.key == "c"
    assert KeyModifier.CTRL in keystroke.modifiers
    assert keystroke.delay_after == timedelta(milliseconds=200)


def test_neovim_command_creation():
    """Verify NeovimCommand model creation."""
    command = NeovimCommand(
        description="Enter insert mode",
        keystrokes=[KeyStroke(key="i")],
    )
    assert command.description == "Enter insert mode"
    assert len(command.keystrokes) == 1
    assert command.wait_for_completion == timedelta(seconds=1)


def test_neovim_test_config_defaults():
    """Verify NeovimTestConfig defaults."""
    config = NeovimTestConfig(commands=[])
    assert config.nvim_config_path == "~/.config/nvim"
    assert config.test_file is None
    assert config.timeout_seconds == 60.0
    assert config.capture_interval == timedelta(milliseconds=500)


def test_neovim_test_config_full():
    """Verify NeovimTestConfig with all fields."""
    commands = [
        NeovimCommand(
            description="Type hello",
            keystrokes=[
                KeyStroke(key="i"),
                KeyStroke(key="h"),
                KeyStroke(key="e"),
                KeyStroke(key="l"),
                KeyStroke(key="l"),
                KeyStroke(key="o"),
            ],
        )
    ]

    config = NeovimTestConfig(
        nvim_config_path="/custom/path",
        test_file="test.txt",
        commands=commands,
        timeout_seconds=120.0,
        capture_interval=timedelta(seconds=1),
    )

    assert config.nvim_config_path == "/custom/path"
    assert config.test_file == "test.txt"
    assert len(config.commands) == 1
    assert config.timeout_seconds == 120.0
    assert config.capture_interval == timedelta(seconds=1)


def test_neovim_test_config_validation():
    """Verify NeovimTestConfig requires commands."""
    with pytest.raises(ValidationError):
        NeovimTestConfig()  # Missing required commands field
