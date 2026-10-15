# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

import os

from pathlib import Path
from typing import Callable, Generator, List, Optional
from shutil import rmtree

from pathspec import GitIgnoreSpec
from aws_doc_sdk_examples_tools.fs import Fs, PathFs


def match_path_to_specs(path: Path, specs: List[GitIgnoreSpec]) -> bool:
    """
    Return True if we should skip this path, that is, it is matched by a .gitignore.

    `path` must be relative to the top-level walk root, mirroring how git
    evaluates `.gitignore` patterns relative to the repository root. Passing an
    absolute path here would let a root-anchored pattern (e.g. `/local`) match a
    leading segment of the checkout's absolute path and spuriously exclude real
    source directories.
    """
    for spec in specs:
        if spec.match_file(path):
            return True
    return False


def walk_with_gitignore(
    root: Path,
    specs: List[GitIgnoreSpec] = [],
    fs: Fs = PathFs(),
    base: Optional[Path] = None,
) -> Generator[Path, None, None]:
    """
    Starting from a root directory, walk the file system yielding a path for each file.
    However, it also reads `.gitignore` files, so that it behaves like `git ls-files`.
    It does not actively use `git ls-files` because it wouldn't catch new files without
    fiddling with a number of flags.

    `base` is the top-level directory the walk started from. It is threaded
    through the recursion so that each path is matched against the accumulated
    `.gitignore` specs *relative to that root*, the way git does. Without this,
    a root-anchored pattern such as `/local` matches the leading segment of an
    absolute checkout path (e.g. `/local/home/<user>/...`) and silently drops
    every file beneath it. Callers should not pass `base` explicitly.
    """
    if base is None:
        base = root

    gitignore = root / ".gitignore"
    gitignore_stat = fs.stat(gitignore)
    if gitignore_stat.exists:
        lines = fs.readlines(gitignore)
        specs = [*specs, GitIgnoreSpec.from_lines(lines)]

    for path in fs.list(root):
        relative_path = path.relative_to(base)
        if not match_path_to_specs(relative_path, specs):
            path_stat = fs.stat(path)
            if path_stat.is_dir:
                yield from walk_with_gitignore(path, specs, fs, base)
            else:
                # Don't yield .gitignore files themselves
                if path.name != ".gitignore":
                    yield path


def get_files(
    root: Path, skip: Callable[[Path], bool] = lambda _: False, fs: Fs = PathFs()
) -> Generator[Path, None, None]:
    """
    Yield non-skipped files, that is, anything not matching git ls-files and not
    in the "to skip" files that are in git but are machine generated, so we don't
    want to validate them.
    """
    for path in walk_with_gitignore(root, fs=fs):
        if not skip(path):
            yield path


def clear(folder: Path):
    if folder.exists():
        rmtree(folder, True)
    folder.mkdir()
