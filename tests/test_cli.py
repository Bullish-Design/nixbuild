"""Tests for CLI interface."""

from __future__ import annotations

from click.testing import CliRunner

from nixos_rebuild_tester.cli import cli


def test_cli_help():
    """Verify CLI help output."""
    runner = CliRunner()
    result = runner.invoke(cli, ["--help"])
    assert result.exit_code == 0
    assert "NixOS rebuild testing" in result.output


def test_run_command_help():
    """Verify run command help."""
    runner = CliRunner()
    result = runner.invoke(cli, ["run", "--help"])
    assert result.exit_code == 0
    assert "Run a NixOS rebuild" in result.output


def test_list_builds_command_help():
    """Verify list-builds command help."""
    runner = CliRunner()
    result = runner.invoke(cli, ["list-builds", "--help"])
    assert result.exit_code == 0
    assert "List recent rebuild attempts" in result.output
