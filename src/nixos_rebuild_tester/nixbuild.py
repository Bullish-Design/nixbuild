"""Minimal nixos-rebuild testing with terminal recording.

Refactored from complex over-engineered architecture to simple direct subprocess approach.
See REFACTORING_GUIDE.md for details.
"""

from __future__ import annotations

import asyncio
import json
import sys
from datetime import datetime
from enum import Enum
from pathlib import Path

import typer

app = typer.Typer(help="NixOS rebuild testing with terminal recording")


class RebuildAction(str, Enum):
    """Available nixos-rebuild actions."""

    TEST = "test"
    BUILD = "build"
    DRY_BUILD = "dry-build"
    DRY_ACTIVATE = "dry-activate"


def _is_remote_flake(flake_ref: str) -> bool:
    """Check if flake reference is remote."""
    remote_prefixes = (
        "github:",
        "gitlab:",
        "git+https:",
        "git+ssh:",
        "https:",
        "tarball+https:",
    )
    return flake_ref.startswith(remote_prefixes)


def _extract_error(output: str) -> str | None:
    """Extract error message from output."""
    for line in output.split("\n"):
        line_lower = line.lower()
        if "error:" in line_lower or "failed" in line_lower:
            return line.strip()[:200]
    return "Build failed with no specific error"


async def run_nixos_rebuild(
    action: RebuildAction,
    flake_ref: str,
    timeout: int,
    output_dir: Path,
) -> tuple[int, Path, str, float]:
    """Run nixos-rebuild and record the session.

    Args:
        action: Rebuild action to perform
        flake_ref: Flake reference to rebuild
        timeout: Maximum rebuild time in seconds
        output_dir: Base directory for outputs

    Returns:
        Tuple of (exit_code, build_dir, error_message, duration)
    """
    # Create unique build directory
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    build_dir = output_dir / f"rebuild-{timestamp}"
    build_dir.mkdir(parents=True, exist_ok=True)

    # Build command
    cmd = ["sudo", "nixos-rebuild", action.value, "--flake", flake_ref]

    # Add flags for remote flakes
    if _is_remote_flake(flake_ref):
        cmd.extend(["--refresh", "--no-write-lock-file"])

    # Setup output files
    log_file = build_dir / "rebuild.log"
    cast_file = build_dir / "session.cast"

    # Wrap with asciinema for recording
    asciinema_cmd = [
        "asciinema",
        "rec",
        "--command",
        " ".join(cmd),
        "--overwrite",
        str(cast_file),
    ]

    # Run command with output capture
    start_time = asyncio.get_event_loop().time()

    try:
        proc = await asyncio.create_subprocess_exec(
            *asciinema_cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,
        )

        stdout_bytes, _ = await asyncio.wait_for(proc.communicate(), timeout=timeout)
        exit_code = proc.returncode or 0
        output = stdout_bytes.decode("utf-8", errors="replace")

    except asyncio.TimeoutError:
        # Kill process on timeout
        try:
            proc.kill()
            await proc.wait()
        except Exception:
            pass
        exit_code = 124  # Standard timeout exit code
        output = "Command timed out"

    duration = asyncio.get_event_loop().time() - start_time

    # Save log
    log_file.write_text(output, encoding="utf-8")

    # Extract error if failed
    error_message = None
    if exit_code != 0:
        error_message = _extract_error(output)

    # Save metadata
    metadata = {
        "success": exit_code == 0,
        "exit_code": exit_code,
        "action": action.value,
        "flake_ref": flake_ref,
        "timestamp": datetime.now().isoformat(),
        "duration_seconds": round(duration, 2),
        "error_message": error_message,
        "artifacts": {
            "log": str(log_file.name),
            "cast": str(cast_file.name) if cast_file.exists() else None,
        },
    }

    metadata_file = build_dir / "metadata.json"
    metadata_file.write_text(json.dumps(metadata, indent=2), encoding="utf-8")

    return exit_code, build_dir, error_message or "", duration


@app.command()
def run(
    action: RebuildAction = typer.Option(RebuildAction.DRY_BUILD, help="Rebuild action to perform"),
    flake: str = typer.Option(".#", help="Flake reference"),
    output_dir: Path = typer.Option(Path("./rebuild-logs"), help="Base directory for outputs"),
    timeout: int = typer.Option(1800, help="Maximum rebuild time in seconds"),
) -> None:
    """Run a NixOS rebuild with recording."""
    typer.echo(f"Starting NixOS rebuild ({action.value}) at {flake}")
    typer.echo(f"Output directory: {output_dir}")
    typer.echo()

    # Run rebuild
    exit_code, build_dir, error_message, duration = asyncio.run(
        run_nixos_rebuild(action, flake, timeout, output_dir)
    )

    # Display results
    if exit_code == 0:
        typer.secho("✓ Rebuild successful", fg=typer.colors.GREEN, bold=True)
    else:
        typer.secho("✗ Rebuild failed", fg=typer.colors.RED, bold=True)
        if error_message:
            typer.echo(f"Error: {error_message}")

    typer.echo(f"\nDuration: {duration:.1f}s")
    typer.echo(f"Exit code: {exit_code}")
    typer.echo(f"\nOutput saved to: {build_dir}")

    # List artifacts
    log_file = build_dir / "rebuild.log"
    cast_file = build_dir / "session.cast"
    if log_file.exists():
        typer.echo(f"  Log: {log_file.name}")
    if cast_file.exists():
        typer.echo(f"  Recording: {cast_file.name}")

    # Exit with same code as rebuild
    sys.exit(exit_code)


@app.command()
def list_builds(
    output_dir: Path = typer.Option(Path("./rebuild-logs"), help="Base directory to list"),
    limit: int = typer.Option(10, help="Number of recent builds to show"),
) -> None:
    """List recent rebuild attempts."""
    base_dir = output_dir.expanduser()

    if not base_dir.exists():
        typer.echo(f"No builds found in {base_dir}")
        return

    # Find all rebuild directories
    rebuild_dirs = sorted(
        [d for d in base_dir.iterdir() if d.is_dir() and d.name.startswith("rebuild-")],
        key=lambda x: x.stat().st_mtime,
        reverse=True,
    )[:limit]

    if not rebuild_dirs:
        typer.echo("No builds found")
        return

    # Display each build
    for build_dir in rebuild_dirs:
        metadata_file = build_dir / "metadata.json"
        if metadata_file.exists():
            with open(metadata_file) as f:
                metadata = json.load(f)

            status = "✓" if metadata["success"] else "✗"
            color = typer.colors.GREEN if metadata["success"] else typer.colors.RED

            typer.secho(f"{status} {build_dir.name}", fg=color, bold=True)
            typer.echo(f"  Action: {metadata['action']}")
            typer.echo(f"  Duration: {metadata['duration_seconds']:.1f}s")
            typer.echo(f"  Timestamp: {metadata['timestamp']}")

            if metadata.get("error_message"):
                typer.echo(f"  Error: {metadata['error_message']}")
            typer.echo()


def main() -> None:
    """Entry point for CLI."""
    app()


if __name__ == "__main__":
    main()
