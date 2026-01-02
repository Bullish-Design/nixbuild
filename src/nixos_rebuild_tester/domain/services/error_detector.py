"""Domain service for detecting errors in build output."""

from __future__ import annotations

import re

from nixos_rebuild_tester.domain.value_objects import ErrorMessage, ErrorSource, Timestamp


class ErrorDetector:
    """Domain service for detecting errors in build output.

    This service encapsulates the logic for extracting error messages
    from various sources (frames, stderr, exit codes).
    """

    # Common error patterns in NixOS rebuild output
    ERROR_PATTERNS = [
        r"error:.*",
        r"failed with exit code.*",
        r"build failed.*",
        r"cannot build.*",
        r"builder for.*failed.*",
        r"assertion failed.*",
    ]

    def extract_from_frames(self, frames: list[str]) -> ErrorMessage | None:
        """Extract error message from terminal frames.

        Searches the last frame for error patterns and returns
        the first match found.

        Args:
            frames: List of terminal frame content strings

        Returns:
            ErrorMessage if error found, None otherwise
        """
        if not frames:
            return None

        # Search last frame for error patterns
        last_frame = frames[-1]
        for pattern in self.ERROR_PATTERNS:
            matches = re.findall(pattern, last_frame, re.IGNORECASE)
            if matches:
                # Truncate to reasonable length
                content = matches[-1][:200]
                return ErrorMessage(
                    content=content,
                    source=ErrorSource.FRAME,
                    timestamp=Timestamp(),
                )

        return None

    def extract_from_exit_code(self, code: int) -> ErrorMessage | None:
        """Extract error message from exit code.

        Args:
            code: Process exit code

        Returns:
            ErrorMessage if code indicates error, None for success
        """
        if code == 0:
            return None

        # Map common exit codes to messages
        messages = {
            1: "Build failed with general error",
            2: "Build failed with configuration error",
            124: "Build timed out",
            127: "Command not found",
            130: "Build interrupted (SIGINT)",
            137: "Build killed (SIGKILL)",
            255: "Application error occurred",
        }

        content = messages.get(code, f"Build failed with exit code {code}")

        return ErrorMessage(
            content=content,
            source=ErrorSource.EXIT_CODE,
            timestamp=Timestamp(),
        )

    def extract_from_stderr(self, stderr: str) -> ErrorMessage | None:
        """Extract error message from stderr output.

        Args:
            stderr: Standard error output

        Returns:
            ErrorMessage if error found, None otherwise
        """
        if not stderr or not stderr.strip():
            return None

        # Search for error patterns
        for pattern in self.ERROR_PATTERNS:
            matches = re.findall(pattern, stderr, re.IGNORECASE)
            if matches:
                content = matches[-1][:200]
                return ErrorMessage(
                    content=content,
                    source=ErrorSource.STDERR,
                    timestamp=Timestamp(),
                )

        # If no pattern matched but stderr has content, use first line
        first_line = stderr.strip().split("\n")[0][:200]
        return ErrorMessage(
            content=first_line,
            source=ErrorSource.STDERR,
            timestamp=Timestamp(),
        )

    def extract_best_error(
        self,
        exit_code: int,
        frames: list[str] | None = None,
        stderr: str | None = None,
    ) -> ErrorMessage | None:
        """Extract the most relevant error from available sources.

        Priority: frames > stderr > exit_code

        Args:
            exit_code: Process exit code
            frames: Optional terminal frames
            stderr: Optional stderr output

        Returns:
            Best available error message, or None if no error
        """
        if exit_code == 0:
            return None

        # Try frames first (most detailed)
        if frames:
            frame_error = self.extract_from_frames(frames)
            if frame_error:
                return frame_error

        # Try stderr next
        if stderr:
            stderr_error = self.extract_from_stderr(stderr)
            if stderr_error:
                return stderr_error

        # Fall back to exit code
        return self.extract_from_exit_code(exit_code)
