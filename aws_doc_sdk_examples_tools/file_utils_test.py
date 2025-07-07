# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

"""
Tests for file_utils.py with filesystem abstraction.
"""

from pathlib import Path

from .fs import RecordFs
from .file_utils import walk_with_gitignore, get_files


class TestWalkWithGitignore:
    """Test walk_with_gitignore with RecordFs."""

    def test_basic_directory_traversal(self):
        """Test basic directory traversal without gitignore."""
        fs = RecordFs(
            {
                Path("root/file1.py"): "print('file1')",
                Path("root/file2.js"): "console.log('file2')",
            }
        )

        files = list(walk_with_gitignore(Path("root"), fs=fs))

        expected = [
            Path("root/file1.py"),
            Path("root/file2.js"),
        ]
        assert sorted(files) == sorted(expected)

    def test_gitignore_filtering(self):
        """Test that gitignore rules are applied correctly."""
        fs = RecordFs(
            {
                Path("root/.gitignore"): "*.tmp\n*.log\n",
                Path("root/keep.py"): "print('keep')",
                Path("root/ignore.tmp"): "temporary",
                Path("root/keep.js"): "console.log('keep')",
                Path("root/debug.log"): "log content",
            }
        )

        files = list(walk_with_gitignore(Path("root"), fs=fs))

        # .gitignore files should not be included in results
        expected = [
            Path("root/keep.py"),
            Path("root/keep.js"),
        ]
        assert sorted(files) == sorted(expected)

    def test_no_gitignore_file(self):
        """Test directory traversal when no .gitignore exists."""
        fs = RecordFs(
            {
                Path("root/file1.py"): "print('file1')",
                Path("root/file2.js"): "console.log('file2')",
                Path("root/file3.txt"): "text content",
            }
        )

        files = list(walk_with_gitignore(Path("root"), fs=fs))

        expected = [
            Path("root/file1.py"),
            Path("root/file2.js"),
            Path("root/file3.txt"),
        ]
        assert sorted(files) == sorted(expected)

    def test_empty_directory(self):
        """Test walking an empty directory."""
        fs = RecordFs({})

        files = list(walk_with_gitignore(Path("empty"), fs=fs))

        assert files == []

    def test_directory_with_only_gitignore(self):
        """Test directory that only contains .gitignore file."""
        fs = RecordFs(
            {
                Path("root/.gitignore"): "*.tmp\n",
            }
        )

        files = list(walk_with_gitignore(Path("root"), fs=fs))

        assert files == []


class TestGetFiles:
    """Test get_files with RecordFs."""

    def test_get_files_basic(self):
        """Test basic get_files functionality."""
        fs = RecordFs(
            {
                Path("root/file1.py"): "print('file1')",
                Path("root/file2.js"): "console.log('file2')",
            }
        )

        files = list(get_files(Path("root"), fs=fs))

        expected = [
            Path("root/file1.py"),
            Path("root/file2.js"),
        ]
        assert sorted(files) == sorted(expected)

    def test_get_files_with_skip_function(self):
        """Test get_files with skip function."""
        fs = RecordFs(
            {
                Path("root/keep.py"): "print('keep')",
                Path("root/skip.py"): "print('skip')",
                Path("root/keep.js"): "console.log('keep')",
                Path("root/skip.js"): "console.log('skip')",
            }
        )

        def skip_function(path: Path) -> bool:
            return "skip" in path.name

        files = list(get_files(Path("root"), skip=skip_function, fs=fs))

        expected = [
            Path("root/keep.py"),
            Path("root/keep.js"),
        ]
        assert sorted(files) == sorted(expected)

    def test_get_files_with_gitignore_and_skip(self):
        """Test get_files with both gitignore and skip function."""
        fs = RecordFs(
            {
                Path("root/.gitignore"): "*.tmp\n",
                Path("root/keep.py"): "print('keep')",
                Path("root/skip.py"): "print('skip')",
                Path("root/ignore.tmp"): "temporary",
                Path("root/keep.js"): "console.log('keep')",
            }
        )

        def skip_function(path: Path) -> bool:
            return "skip" in path.name

        files = list(get_files(Path("root"), skip=skip_function, fs=fs))

        expected = [
            Path("root/keep.py"),
            Path("root/keep.js"),
        ]
        assert sorted(files) == sorted(expected)
