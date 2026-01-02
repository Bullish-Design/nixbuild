"""Core rebuild execution with terminal recording."""

from __future__ import annotations

import asyncio
import json
import re
import shutil
import time
from datetime import datetime
from pathlib import Path

from terminal_state.export.asciinema import AsciinemaExporter
from terminal_state.export.gif import GifExporter
from terminal_state.export.screenshot import ScreenshotExporter
from terminal_state.models.config import SessionConfig
from terminal_state.session.terminal import TerminalSession

from nixos_rebuild_tester.models import Config, RebuildResult


class RebuildRunner:
    """Executes NixOS rebuilds with terminal recording."""

    def __init__(self, config: Config):
        """Initialize runner with configuration.

        Args:
            config: Complete configuration object
        """
        self.config = config

    async def run(self) -> RebuildResult:
        """Execute complete rebuild workflow.

        Returns:
            RebuildResult with complete information about the rebuild

        Note:
            This method never raises exceptions - all errors are captured
            in the RebuildResult with appropriate exit codes.
        """
        output_dir = self._create_output_dir()

        try:
            result = await self._run_rebuild_with_recording(output_dir)
        except Exception as e:
            # Never crash - always return a result
            result = RebuildResult(
                success=False,
                exit_code=255,
                timestamp=datetime.now(),
                duration_seconds=0.0,
                action=self.config.rebuild.action,
                output_dir=output_dir,
                log_file=output_dir / "rebuild.log",
                error_message=f"Runner error: {str(e)}",
            )

        # Cleanup old builds after success/failure
        self._cleanup_old_builds()

        return result

    def _create_output_dir(self) -> Path:
        """Create timestamped output directory.

        Returns:
            Path to created directory
        """
        timestamp = datetime.now().strftime(self.config.output.timestamp_format)
        output_dir = self.config.output.base_dir.expanduser() / f"rebuild-{timestamp}"
        output_dir.mkdir(parents=True, exist_ok=True)
        return output_dir

    def _cleanup_old_builds(self) -> None:
        """Remove old build directories if configured."""
        if self.config.output.keep_last_n is None:
            return

        base_dir = self.config.output.base_dir.expanduser()
        if not base_dir.exists():
            return

        rebuild_dirs = sorted(
            [d for d in base_dir.iterdir() if d.is_dir() and d.name.startswith("rebuild-")],
            key=lambda x: x.stat().st_mtime,
            reverse=True,
        )

        for old_dir in rebuild_dirs[self.config.output.keep_last_n :]:
            shutil.rmtree(old_dir)

    async def _run_rebuild_with_recording(self, output_dir: Path) -> RebuildResult:
        """Run rebuild with terminal recording.

        Args:
            output_dir: Directory to save artifacts

        Returns:
            RebuildResult with complete information
        """
        start_time = time.time()
        timestamp = datetime.now()

        # Determine file paths
        log_file = output_dir / "rebuild.log"
        cast_file = output_dir / "rebuild.cast" if self.config.recording.enabled else None
        gif_file = output_dir / "rebuild.gif" if self.config.recording.export_gif else None
        screenshot_file = output_dir / "final.png" if self.config.recording.export_screenshot else None

        exit_code = 0
        error_message = None

        # Configure terminal session
        session_config = SessionConfig(
            width=self.config.recording.width,
            height=self.config.recording.height,
        )

        # Run in terminal session (context manager auto-cleans up)
        with TerminalSession(session_config) as session:
            # Build the rebuild command
            rebuild_cmd = (
                f"sudo nixos-rebuild {self.config.rebuild.action.value} " f"--flake {self.config.rebuild.flake_ref}"
            )

            # Send command (record=True adds frame to recording)
            session.send_command(rebuild_cmd, record=True)

            # Wait for output to appear
            try:
                if not session.expect_text(
                    r"(building|activating|copying|warning|error|failed)",
                    timeout=self.config.rebuild.timeout_seconds,
                ):
                    error_message = "Rebuild timed out or produced no output"
                    exit_code = 124  # Standard timeout exit code

                # Let output settle
                await asyncio.sleep(2)

                # Capture final state
                final_frame = session.capture()
                session.recording.add_frame(final_frame)

                # Check for errors in output
                if "error" in final_frame.content.lower() or "failed" in final_frame.content.lower():
                    exit_code = 1
                    error_message = self._extract_error_from_frame(final_frame.content)

            except Exception as e:
                exit_code = 1
                error_message = str(e)

            # Export artifacts
            # 1. Text log (always)
            with open(log_file, "w") as f:
                for frame in session.recording.frames:
                    f.write(frame.content)
                    f.write("\n" + "=" * 80 + "\n")

            # 2. Asciinema recording (if enabled)
            if cast_file and session.recording.frames:
                exporter = AsciinemaExporter()
                exporter.export(session.recording, cast_file)

            # 3. Final screenshot (if enabled)
            if screenshot_file and session.recording.frames:
                screenshot_exporter = ScreenshotExporter()
                screenshot_exporter.export_frame(session.recording.frames[-1], screenshot_file)

            # 4. GIF animation (if enabled)
            if gif_file and session.recording.frames:
                gif_exporter = GifExporter()
                gif_exporter.export(session.recording, gif_file)

        # Calculate duration
        duration = time.time() - start_time

        # Build result object
        result = RebuildResult(
            success=exit_code == 0,
            exit_code=exit_code,
            timestamp=timestamp,
            duration_seconds=duration,
            action=self.config.rebuild.action,
            output_dir=output_dir,
            log_file=log_file,
            cast_file=cast_file,
            gif_file=gif_file,
            screenshot_file=screenshot_file,
            error_message=error_message,
        )

        # Save metadata
        self._save_metadata(output_dir, result)

        return result

    def _extract_error_from_frame(self, content: str) -> str:
        """Extract error message from terminal content.

        Args:
            content: Terminal content to search

        Returns:
            Error message string (truncated to 200 chars)

        Note:
            This is fragile - terminal output parsing is inherently unreliable.
        """
        error_pattern = r"error:.*"
        matches = re.findall(error_pattern, content, re.IGNORECASE)
        if matches:
            return matches[-1][:200]
        return "Build failed (see logs for details)"

    def _save_metadata(self, output_dir: Path, result: RebuildResult) -> None:
        """Save rebuild metadata to JSON.

        Args:
            output_dir: Directory to save metadata in
            result: Result to serialize
        """
        metadata_file = output_dir / "metadata.json"
        metadata = {
            "success": result.success,
            "exit_code": result.exit_code,
            "timestamp": result.timestamp.isoformat(),
            "duration_seconds": result.duration_seconds,
            "action": result.action.value,
            "error_message": result.error_message,
            "files": {
                "log": str(result.log_file.relative_to(output_dir)),
                "cast": str(result.cast_file.relative_to(output_dir)) if result.cast_file else None,
                "gif": str(result.gif_file.relative_to(output_dir)) if result.gif_file else None,
                "screenshot": str(result.screenshot_file.relative_to(output_dir)) if result.screenshot_file else None,
            },
        }

        with open(metadata_file, "w") as f:
            json.dump(metadata, f, indent=2)
