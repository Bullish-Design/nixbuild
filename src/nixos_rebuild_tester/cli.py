"""Command-line interface for NixOS rebuild tester."""

from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path

import click

from nixos_rebuild_tester.models import Config, OutputConfig, RebuildAction, RebuildConfig, RecordingConfig
from nixos_rebuild_tester.runner import RebuildRunner


@click.group()
def cli() -> None:
    """NixOS rebuild testing with terminal recording."""
    pass


@cli.command()
@click.option(
    "--action",
    type=click.Choice([a.value for a in RebuildAction]),
    default=RebuildAction.TEST.value,
    help="Rebuild action to perform",
)
@click.option("--flake", default=".#", help="Flake reference")
@click.option("--output-dir", type=click.Path(), default="./rebuild-logs", help="Base directory for outputs")
@click.option("--keep-last", type=int, default=None, help="Keep only last N builds")
@click.option("--no-recording", is_flag=True, help="Disable terminal recording")
@click.option("--export-gif", is_flag=True, help="Export GIF animation")
@click.option("--timeout", type=int, default=1800, help="Maximum rebuild time in seconds")
def run(
    action: str,
    flake: str,
    output_dir: str,
    keep_last: int | None,
    no_recording: bool,
    export_gif: bool,
    timeout: int,
) -> None:
    """Run a NixOS rebuild with recording."""
    # Build config from CLI args
    config = Config(
        recording=RecordingConfig(
            enabled=not no_recording,
            export_gif=export_gif,
        ),
        rebuild=RebuildConfig(
            action=RebuildAction(action),
            flake_ref=flake,
            timeout_seconds=timeout,
        ),
        output=OutputConfig(
            base_dir=Path(output_dir),
            keep_last_n=keep_last,
        ),
    )

    runner = RebuildRunner(config)

    click.echo(f"Starting NixOS rebuild ({action}) at {config.rebuild.flake_ref}")
    click.echo(f"Output directory: {config.output.base_dir}")
    click.echo()

    # Run async function in sync context
    result = asyncio.run(runner.run())

    # Display results
    if result.success:
        click.secho("✓ Rebuild successful", fg="green", bold=True)
    else:
        click.secho("✗ Rebuild failed", fg="red", bold=True)
        if result.error_message:
            click.echo(f"Error: {result.error_message}")

    click.echo(f"\nDuration: {result.duration_seconds:.1f}s")
    click.echo(f"Exit code: {result.exit_code}")
    click.echo(f"\nOutput saved to: {result.output_dir}")
    click.echo(f"  Log: {result.log_file.name}")
    if result.cast_file:
        click.echo(f"  Recording: {result.cast_file.name}")
    if result.screenshot_file:
        click.echo(f"  Screenshot: {result.screenshot_file.name}")
    if result.gif_file:
        click.echo(f"  GIF: {result.gif_file.name}")

    # Exit with same code as rebuild
    sys.exit(0 if result.success else result.exit_code)


@cli.command()
@click.option("--output-dir", type=click.Path(exists=True), default="./rebuild-logs", help="Base directory to list")
@click.option("--limit", type=int, default=10, help="Number of recent builds to show")
def list_builds(output_dir: str, limit: int) -> None:
    """List recent rebuild attempts."""
    base_dir = Path(output_dir).expanduser()

    if not base_dir.exists():
        click.echo(f"No builds found in {base_dir}")
        return

    # Find all rebuild directories
    rebuild_dirs = sorted(
        [d for d in base_dir.iterdir() if d.is_dir() and d.name.startswith("rebuild-")],
        key=lambda x: x.stat().st_mtime,
        reverse=True,
    )[:limit]

    if not rebuild_dirs:
        click.echo("No builds found")
        return

    # Display each build
    for build_dir in rebuild_dirs:
        metadata_file = build_dir / "metadata.json"
        if metadata_file.exists():
            with open(metadata_file) as f:
                metadata = json.load(f)

            status = "✓" if metadata["success"] else "✗"
            color = "green" if metadata["success"] else "red"

            click.secho(f"{status} {build_dir.name}", fg=color, bold=True)
            click.echo(f"  Action: {metadata['action']}")
            click.echo(f"  Duration: {metadata['duration_seconds']:.1f}s")
            click.echo(f"  Timestamp: {metadata['timestamp']}")
            if metadata.get("error_message"):
                click.echo(f"  Error: {metadata['error_message']}")
            click.echo()


def main() -> None:
    """Entry point for CLI."""
    cli()


if __name__ == "__main__":
    main()
