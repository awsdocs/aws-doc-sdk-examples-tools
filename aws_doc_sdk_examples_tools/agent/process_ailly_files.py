"""
Parse generated Ailly output for key: value pairs.

This module processes *.md.ailly.md files, extracts key-value pairs,
converts them to JSON entries in an array, and writes the JSON array
to a specified output file.
"""

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Set

logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)

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

        result["title_abbrev"] = result["title"]
        result["id"] = Path(file_path).name.split(".md.ailly.md")[0]
        result["_source_file"] = file_path

    except Exception as e:
        logger.error(f"Error parsing file {file_path}", exc_info=e)

    return result


def process_ailly_files(
    input_dir: str, output_file: str, file_pattern: str = "*.md.ailly.md"
) -> None:
    """
    Process all .md.ailly.md files in the input directory and write the results as JSON to the output file.

    Args:
        input_dir: Directory containing .md.ailly.md files
        output_file: Path to the output JSON file
        file_pattern: Pattern to match files (default: "*.md.ailly.md")
    """
    results = []
    input_path = Path(input_dir)

    try:
        for file_path in input_path.glob(file_pattern):
            logger.info(f"Processing file: {file_path}")
            parsed_data = parse_ailly_file(str(file_path))
            if parsed_data:
                results.append(parsed_data)

        with open(output_file, "w", encoding="utf-8") as out_file:
            json.dump(results, out_file, indent=2)

        logger.info(
            f"Successfully processed {len(results)} files. Output written to {output_file}"
        )

    except Exception as e:
        logger.error("Error processing files", exc_info=e)
