# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

"""
Tests for the Fs interface, particularly the readlines functionality.
"""

import pytest
import tempfile
from pathlib import Path
from typing import List

from .fs import Fs, PathFs, RecordFs


def assert_readlines_result(fs: Fs, path: Path, expected: List[str]):
    """Generic assertion for readlines results."""
    lines = fs.readlines(path)
    assert lines == expected
    assert len(lines) == len(expected)


def run_common_readlines_scenarios(fs: Fs, path_factory):
    """Test common readlines scenarios for any Fs implementation."""
    # Basic multi-line content
    path = path_factory("Line 1\nLine 2\nLine 3\n")
    assert_readlines_result(fs, path, ["Line 1\n", "Line 2\n", "Line 3\n"])

    # Empty file
    path = path_factory("")
    assert_readlines_result(fs, path, [])

    # No final newline
    path = path_factory("Line 1\nLine 2")
    assert_readlines_result(fs, path, ["Line 1\n", "Line 2"])

    # Single line
    path = path_factory("Single line\n")
    assert_readlines_result(fs, path, ["Single line\n"])


class TestPathFs:
    """Test PathFs implementation of readlines."""

    def test_readlines_scenarios(self):
        """Test various readlines scenarios with PathFs."""
        fs = PathFs()
        temp_files = []

        def path_factory(content: str) -> Path:
            with tempfile.NamedTemporaryFile(
                mode="w", delete=False, suffix=".txt"
            ) as f:
                f.write(content)
                path = Path(f.name)
                temp_files.append(path)
                return path

        try:
            run_common_readlines_scenarios(fs, path_factory)
        finally:
            # Clean up temp files
            errors = []
            for path in temp_files:
                try:
                    if path.exists():
                        path.unlink()
                except Exception as e:
                    errors.append((path, e))
            if errors:
                messages = "\n".join(
                    f"{path}: {type(e).__name__}: {e}" for path, e in errors
                )
                pytest.fail(
                    f"Errors occurred while cleaning up temp files:\n{messages}"
                )


class TestRecordFs:
    """Test RecordFs implementation of readlines."""

    def test_readlines_scenarios(self):
        """Test various readlines scenarios with RecordFs."""
        test_cases = [
            ("Line 1\nLine 2\nLine 3\n", ["Line 1\n", "Line 2\n", "Line 3\n"]),
            ("", []),
            ("Line 1\nLine 2", ["Line 1\n", "Line 2"]),
            ("Single line\n", ["Single line\n"]),
        ]

        for content, expected in test_cases:
            fs = RecordFs({Path("test.txt"): content})
            assert_readlines_result(fs, Path("test.txt"), expected)

    def test_readlines_line_ending_variations(self):
        """Test readlines with different line ending styles."""
        test_cases = [
            (
                "Line 1\r\nLine 2\r\nLine 3\r\n",
                ["Line 1\r\n", "Line 2\r\n", "Line 3\r\n"],
            ),
            ("Line 1\nLine 2\r\nLine 3\n", ["Line 1\n", "Line 2\r\n", "Line 3\n"]),
        ]

        for content, expected in test_cases:
            fs = RecordFs({Path("test.txt"): content})
            assert_readlines_result(fs, Path("test.txt"), expected)
