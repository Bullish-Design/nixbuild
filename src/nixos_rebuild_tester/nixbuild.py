# src/nixos_rebuild_tester/nixbuild.py
"""Minimal nixos-rebuild testing with terminal recording.

Refactored from complex over-engineered architecture to simple direct subprocess approach.
See REFACTORING_GUIDE.md for details.
"""

from __future__ import annotations

import asyncio
import json
import shutil
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


def _extract_text_from_cast(cast_file: Path) -> str:
    """Extract text content from asciinema .cast file."""
    try:
        with open(cast_file) as f:
            lines = []
            for line in f:
                if not line.strip():
                    continue
                try:
                    event = json.loads(line)
                    if isinstance(event, list) and len(event) >= 3 and event[1] == "o":
                        lines.append(event[2])
                except json.JSONDecodeError:
                    continue
            return "".join(lines)
    except Exception as e:
        return f"Failed to extract text from recording: {e}"


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
    output_dir = output_dir.expanduser().resolve()
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    build_dir = output_dir / f"rebuild-{timestamp}"

    try:
        build_dir.mkdir(parents=True, exist_ok=True)
    except (PermissionError, OSError) as e:
        raise RuntimeError(f"Failed to create output directory {build_dir}: {e}") from e

    cmd = ["sudo", "nixos-rebuild", action.value, "--flake", flake_ref]

    if _is_remote_flake(flake_ref):
        cmd.extend(["--refresh", "--no-write-lock-file"])

    log_file = build_dir / "rebuild.log"
    cast_file = build_dir / "session.cast"

    asciinema_cmd = [
        "asciinema",
        "rec",
        "--command",
        " ".join(cmd),
        "--overwrite",
        str(cast_file),
    ]

    start_time = asyncio.get_event_loop().time()
    proc = None
    exit_code = 1
    error_occurred = False
    error_message_raw = ""

    try:
        proc = await asyncio.create_subprocess_exec(*asciinema_cmd)
        exit_code_result = await asyncio.wait_for(proc.wait(), timeout=timeout)
        exit_code = exit_code_result if exit_code_result is not None else 1

    except asyncio.TimeoutError:
        if proc:
            try:
                proc.kill()
                await proc.wait()
            except Exception:
                pass
        exit_code = 124
        error_occurred = True
        error_message_raw = "Command timed out"

    except FileNotFoundError as e:
        exit_code = 127
        error_occurred = True
        error_message_raw = f"Command not found: {e.filename}\n\nPlease ensure 'asciinema' is installed."

    except PermissionError as e:
        exit_code = 126
        error_occurred = True
        error_message_raw = f"Permission denied: {e}"

    except Exception as e:
        exit_code = 1
        error_occurred = True
        error_message_raw = f"Unexpected error: {type(e).__name__}: {e}"

    duration = asyncio.get_event_loop().time() - start_time

    # Extract text from recording for log file
    if cast_file.exists() and not error_occurred:
        output_text = _extract_text_from_cast(cast_file)
    else:
        output_text = error_message_raw

    try:
        log_file.write_text(output_text, encoding="utf-8")
    except (PermissionError, OSError) as e:
        typer.secho(
            f"Warning: Failed to write log file {log_file}: {e}",
            fg=typer.colors.YELLOW,
            err=True,
        )

    error_message = None
    if exit_code != 0:
        error_message = _extract_error(output_text) if not error_occurred else error_message_raw

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
    try:
        metadata_file.write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    except (PermissionError, OSError) as e:
        typer.secho(
            f"Warning: Failed to write metadata file {metadata_file}: {e}",
            fg=typer.colors.YELLOW,
            err=True,
        )

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

    exit_code, build_dir, error_message, duration = asyncio.run(
        run_nixos_rebuild(action, flake, timeout, output_dir)
    )

    if exit_code == 0:
        typer.secho("✓ Rebuild successful", fg=typer.colors.GREEN, bold=True)
    else:
        typer.secho("✗ Rebuild failed", fg=typer.colors.RED, bold=True)
        if error_message:
            typer.echo(f"Error: {error_message}")

    typer.echo(f"\nDuration: {duration:.1f}s")
    typer.echo(f"Exit code: {exit_code}")
    typer.echo(f"\nOutput saved to: {build_dir}")

    log_file = build_dir / "rebuild.log"
    cast_file = build_dir / "session.cast"
    if log_file.exists():
        typer.echo(f"  Log: {log_file.name}")
    if cast_file.exists():
        typer.echo(f"  Recording: {cast_file.name}")
        typer.echo(f"\nPlay with: nixos-rebuild-test play {cast_file}")

    sys.exit(exit_code)


@app.command()
def play(
    cast_file: Path = typer.Argument(..., help="Path to .cast file to play"),
    speed: float = typer.Option(1.0, help="Playback speed multiplier"),
    idle_time_limit: float = typer.Option(None, help="Limit idle time to N seconds"),
) -> None:
    """Play back an asciinema recording."""
    cast_file = cast_file.expanduser().resolve()

    if not cast_file.exists():
        typer.secho(f"Error: File not found: {cast_file}", fg=typer.colors.RED, err=True)
        raise typer.Exit(1)

    if not cast_file.suffix == ".cast":
        typer.secho(f"Warning: Expected .cast file, got {cast_file.suffix}", fg=typer.colors.YELLOW)

    asciinema_path = shutil.which("asciinema")
    if not asciinema_path:
        typer.secho("Error: asciinema not found in PATH", fg=typer.colors.RED, err=True)
        typer.echo("This shouldn't happen - asciinema should be bundled with nixos-rebuild-test")
        raise typer.Exit(1)

    cmd = [asciinema_path, "play", str(cast_file)]

    if speed != 1.0:
        cmd.extend(["--speed", str(speed)])

    if idle_time_limit is not None:
        cmd.extend(["--idle-time-limit", str(idle_time_limit)])

    try:
        import subprocess

        result = subprocess.run(cmd, check=False)
        sys.exit(result.returncode)
    except KeyboardInterrupt:
        typer.echo("\nPlayback interrupted")
        sys.exit(0)
    except Exception as e:
        typer.secho(f"Error playing recording: {e}", fg=typer.colors.RED, err=True)
        raise typer.Exit(1)


@app.command()
def list_builds(
    output_dir: Path = typer.Option(Path("./rebuild-logs"), help="Base directory to list"),
    limit: int = typer.Option(10, help="Number of recent builds to show"),
) -> None:
    """List recent rebuild attempts."""
    base_dir = output_dir.expanduser().resolve()

    if not base_dir.exists():
        typer.echo(f"No builds found in {base_dir}")
        return

    try:
        rebuild_dirs = sorted(
            [d for d in base_dir.iterdir() if d.is_dir() and d.name.startswith("rebuild-")],
            key=lambda x: x.stat().st_mtime,
            reverse=True,
        )[:limit]
    except (PermissionError, OSError) as e:
        typer.secho(f"Error accessing directory {base_dir}: {e}", fg=typer.colors.RED, err=True)
        return

    if not rebuild_dirs:
        typer.echo("No builds found")
        return

    for build_dir in rebuild_dirs:
        metadata_file = build_dir / "metadata.json"
        if metadata_file.exists():
            try:
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

                cast_file = build_dir / metadata["artifacts"]["cast"]
                if cast_file.exists():
                    typer.echo(f"  Play: nixos-rebuild-test play {cast_file}")

                typer.echo()
            except (PermissionError, OSError, json.JSONDecodeError) as e:
                typer.secho(
                    f"Warning: Failed to read metadata for {build_dir.name}: {e}",
                    fg=typer.colors.YELLOW,
                    err=True,
                )


def main() -> None:
    """Entry point for CLI."""
    app()


if __name__ == "__main__":
    main()
