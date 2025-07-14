import json
import logging
import time
from collections import defaultdict
from dataclasses import dataclass
from datetime import timedelta
from pathlib import Path
from subprocess import run
from typing import Any, Dict, List, Optional, Set

from aws_doc_sdk_examples_tools.lliam.domain.commands import RunAilly
from aws_doc_sdk_examples_tools.lliam.domain.errors import (
    CommandExecutionError,
    DomainError,
)
from aws_doc_sdk_examples_tools.lliam.config import (
    AILLY_DIR_PATH,
    BATCH_PREFIX,
)

AILLY_CMD_BASE = [
    "ailly",
    "--max-depth",
    "10",
    "--root",
    str(AILLY_DIR_PATH),
]

logger = logging.getLogger(__file__)


def handle_run_ailly(cmd: RunAilly, uow: None):
    resolved_batches = resolve_requested_batches(cmd.batches)

    errors: List[DomainError] = []

    if resolved_batches:
        total_start_time = time.time()

        for batch in resolved_batches:
            try:
                run_ailly_single_batch(batch, cmd.packages)
            except FileNotFoundError as e:
                errors.append(
                    CommandExecutionError(
                        command_name=cmd.__class__.__name__, message=str(e)
                    )
                )

        total_end_time = time.time()
        total_duration = total_end_time - total_start_time
        num_batches = len(resolved_batches)
        logger.info(
            f"[TIMECHECK] {num_batches} batches took {format_duration(total_duration)} to run"
        )

    return errors


def resolve_requested_batches(batch_names: List[str]) -> List[Path]:
    if not batch_names:
        batch_paths = [
            p
            for p in AILLY_DIR_PATH.iterdir()
            if p.is_dir() and p.name.startswith(BATCH_PREFIX)
        ]

        return batch_paths

    batch_paths = []

    for batch_name in batch_names:
        batch_path = Path(AILLY_DIR_PATH / batch_name)
        if not batch_path.exists():
            raise FileNotFoundError(batch_path)
        if not batch_path.is_dir():
            raise NotADirectoryError(batch_path)
        batch_paths.append(batch_path)

    return batch_paths


def run_ailly_single_batch(batch: Path, packages: List[str] = []) -> None:
    """Run ailly and process files for a single batch."""
    batch_start_time = time.time()
    iam_updates_path = AILLY_DIR_PATH / f"updates_{batch.name}.json"

    if packages:
        paths = []
        for package in packages:
            package_files = [
                f"{batch.name}/{p.name}" for p in batch.glob(f"*{package}*.md")
            ]
            paths.extend(package_files)

        if not paths:
            raise FileNotFoundError(f"No matching files found for packages: {packages}")

        cmd = AILLY_CMD_BASE + paths
    else:
        cmd = AILLY_CMD_BASE + [batch.name]

    logger.info(f"Running {cmd}")
    run(cmd)

    batch_end_time = time.time()
    batch_duration = batch_end_time - batch_start_time
    logger.info(
        f"[TIMECHECK] {batch.name} took {format_duration(batch_duration)} to run"
    )

    logger.info(f"Processing generated content for {batch.name}")
    process_ailly_files(
        input_dir=batch, output_file=iam_updates_path, packages=packages
    )


EXPECTED_KEYS: Set[str] = set(["title", "title_abbrev"])
VALUE_PREFIXES: Dict[str, str] = {"title": "", "title_abbrev": "", "synopsis": ""}


class MissingExpectedKeys(Exception):
    pass


def parse_fenced_blocks(content: str, fence="===") -> List[List[str]]:
    blocks = []
    inside_fence = False
    current_block: List[str] = []

    for line in content.splitlines():
        if line.strip() == fence:
            if inside_fence:
                blocks.append(current_block)
                current_block = []
            inside_fence = not inside_fence
        elif inside_fence:
            current_block.append(line)

    return blocks


def parse_block_lines(
    block: List[str], key_pairs: Dict[str, str], expected_keys=EXPECTED_KEYS
):
    for line in block:
        if "=>" in line:
            parts = line.split("=>", 1)
            key = parts[0].strip()
            value = parts[1].strip() if len(parts) > 1 else ""
            key_pairs[key] = value
    if missing_keys := expected_keys - key_pairs.keys():
        raise MissingExpectedKeys(missing_keys)


def parse_ailly_file(
    file_path: str, value_prefixes: Dict[str, str] = VALUE_PREFIXES
) -> Dict[str, Any]:
    """
    Parse an .md.ailly.md file and extract key-value pairs that are between === fence markers. Each
    key value pair is assumed to be on one line and in the form of `key => value`. This formatting is
    totally dependent on the LLM output written by Ailly.

    Args:
        file_path: Path to the .md.ailly.md file

    Returns:
        Dictionary containing the extracted key-value pairs
    """
    result: Dict[str, str] = {}

    try:
        with open(file_path, "r", encoding="utf-8") as file:
            content = file.read()

        blocks = parse_fenced_blocks(content)

        for block in blocks:
            parse_block_lines(block, result)

        for key, prefix in value_prefixes.items():
            if key in result:
                result[key] = f"{prefix}{result[key]}"

        result["id"] = Path(file_path).name.split(".md.ailly.md")[0]
        result["_source_file"] = file_path

    except Exception as e:
        logger.error(f"Error parsing file {file_path}", exc_info=e)

    return result


def parse_package_name(policy_update: Dict[str, str]) -> Optional[str]:
    if not policy_update:
        return None

    if not isinstance(policy_update, dict):
        return None

    if not (id := policy_update.get("id")):
        return None

    id_parts = [part.strip() for part in id.split(".")]

    if id_parts[0] != "iam-policies":
        return None

    return id_parts[1]  # The package name, hopefully.


def process_ailly_files(
    input_dir: Path,
    output_file: Path,
    file_pattern: str = "*.md.ailly.md",
    packages: List[str] = [],
) -> None:
    """
    Process all .md.ailly.md files in the input directory and write the results as JSON to the output file.

    Args:
        input_dir: Directory containing .md.ailly.md files
        output_file: Path to the output JSON file
        file_pattern: Pattern to match files (default: "*.md.ailly.md")
        packages: Optional list of packages to filter by
    """
    results = defaultdict(list)

    try:
        for file_path in input_dir.rglob(file_pattern):
            logger.info(f"Processing file: {file_path}")
            policy_update = parse_ailly_file(str(file_path))
            if policy_update:
                package_name = parse_package_name(policy_update)
                if not package_name:
                    raise TypeError(f"Could not get package name from policy update.")

                if packages and package_name not in packages:
                    logger.info(
                        f"Skipping package {package_name} (not in requested packages)"
                    )
                    continue

                results[package_name].append(policy_update)

        with open(output_file, "w", encoding="utf-8") as out_file:
            json.dump(results, out_file, indent=2)

        logger.info(
            f"Successfully processed files. Output written to {output_file.name}"
        )

    except Exception as e:
        logger.error("Error processing files", exc_info=e)


def format_duration(seconds: float) -> str:
    td = timedelta(seconds=seconds)
    return str(td).zfill(8)
