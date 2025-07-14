#!/usr/bin/env python3
"""
Script to process .md and .ailly.md file pairs and generate JSONL output.

This script:
1. Collects file data from .md and .ailly.md pairs
2. Extracts content without front matter
3. Generates JSONL output with prompt and model responses
"""

import os
import json
import re
import argparse
from pathlib import Path
from typing import Dict, List, Tuple, Optional


def collect_file_pairs(
    directory: str, limit: Optional[int] = None
) -> List[Tuple[str, str]]:
    """
    Collect pairs of .md and .ailly.md files from the specified directory.

    Args:
        directory: Path to the directory containing the files
        limit: Optional limit on the number of pairs to process

    Returns:
        List of tuples containing (md_file_path, ailly_md_file_path)
    """
    md_files = {}
    ailly_md_files = {}

    # Walk through the directory and collect all .md and .ailly.md files
    for root, _, files in os.walk(directory):
        for file in files:
            file_path = os.path.join(root, file)
            if file.endswith(".md") and not file.endswith(".ailly.md"):
                md_files[file] = file_path
            elif file.endswith(".ailly.md"):
                base_name = file[:-9]  # Remove '.ailly.md'
                ailly_md_files[base_name] = file_path

    # Match the pairs
    pairs = []
    for base_name, md_path in md_files.items():
        if base_name in ailly_md_files:
            pairs.append((md_path, ailly_md_files[base_name]))

    # Apply limit if specified
    if limit is not None and limit > 0:
        pairs = pairs[:limit]

    return pairs


def extract_content(file_path: str) -> str:
    """
    Extract content from a file, removing any front matter.

    Args:
        file_path: Path to the file

    Returns:
        Content of the file without front matter
    """
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Remove front matter if it exists (content between --- markers)
    front_matter_pattern = r"^---\n.*?\n---\n"
    content = re.sub(front_matter_pattern, "", content, flags=re.DOTALL)

    return content.strip()


def get_aillyrc_content(directory: str) -> str:
    """
    Get the content of the .aillyrc file without the front matter.

    Args:
        directory: Directory containing the .aillyrc file

    Returns:
        Content of the .aillyrc file without front matter
    """
    # Find the .aillyrc file by going up directories if needed
    current_dir = directory
    aillyrc_path = None

    while current_dir and current_dir != "/":
        potential_path = os.path.join(current_dir, ".aillyrc")
        if os.path.exists(potential_path):
            aillyrc_path = potential_path
            break
        current_dir = os.path.dirname(current_dir)

    if not aillyrc_path:
        raise FileNotFoundError("Could not find .aillyrc file")

    return extract_content(aillyrc_path)


def extract_model_identifier(ailly_file_path: str) -> Dict:
    """
    Extract model identifier from the .ailly.md file's front matter.

    Args:
        ailly_file_path: Path to the .ailly.md file

    Returns:
        Dictionary containing model identifier information
    """
    with open(ailly_file_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Extract front matter
    front_matter_match = re.search(r"^---\n(.*?)\n---\n", content, re.DOTALL)
    if not front_matter_match:
        return {}

    front_matter = front_matter_match.group(1)

    # Extract debug information
    debug_match = re.search(r"debug:\s*\n(.*?)(\n\w|$)", front_matter, re.DOTALL)
    if not debug_match:
        return {}

    debug_content = debug_match.group(1)

    # Extract model information
    model_match = re.search(r"model:\s*(.*?)$", debug_content, re.MULTILINE)
    region_match = re.search(r"region:\s*(.*?)$", debug_content, re.MULTILINE)

    model_identifier = {}
    if model_match:
        model_identifier["model"] = model_match.group(1).strip()
    if region_match:
        model_identifier["region"] = region_match.group(1).strip()

    return model_identifier


def convert_to_jsonl_format(
    file_pairs: List[Tuple[str, str]], aillyrc_content: str
) -> List[Dict]:
    """
    Convert file pairs to JSONL format.

    Args:
        file_pairs: List of (md_file_path, ailly_md_file_path) tuples
        aillyrc_content: Content of the .aillyrc file

    Returns:
        List of dictionaries in the required format
    """
    jsonl_entries = []

    for md_path, ailly_md_path in file_pairs:
        # Extract content from files
        md_content = extract_content(md_path)
        ailly_md_content = extract_content(ailly_md_path)

        # Extract model identifier
        model_identifier = extract_model_identifier(ailly_md_path)

        # Create JSONL entry
        entry = {
            "prompt": aillyrc_content + "\n\n" + md_content,
            "modelResponses": [
                {"response": ailly_md_content, "modelIdentifier": model_identifier}
            ],
        }

        jsonl_entries.append(entry)

    return jsonl_entries


def write_jsonl_file(entries: List[Dict], output_path: str) -> None:
    """
    Write entries to a JSONL file.

    Args:
        entries: List of dictionaries to write
        output_path: Path to the output file
    """
    with open(output_path, "w", encoding="utf-8") as f:
        for entry in entries:
            f.write(json.dumps(entry) + "\n")


def main():
    """Main function to process files and generate JSONL output."""
    parser = argparse.ArgumentParser(
        description="Process .md and .ailly.md file pairs and generate JSONL output."
    )
    parser.add_argument(
        "--directory",
        "-d",
        type=str,
        default=".ailly_iam_policy/batch_01",
        help="Directory containing the file pairs",
    )
    parser.add_argument(
        "--output",
        "-o",
        type=str,
        default="output.jsonl",
        help="Path to the output JSONL file",
    )
    parser.add_argument(
        "--limit",
        "-n",
        type=int,
        default=None,
        help="Limit the number of file pairs to process",
    )

    args = parser.parse_args()

    # Resolve paths
    base_dir = os.path.dirname(os.path.abspath(__file__))
    directory = os.path.join(base_dir, args.directory)
    output_path = os.path.join(base_dir, args.output)

    # Step 1: Collect file pairs
    print(f"Collecting file pairs from {directory}...")
    file_pairs = collect_file_pairs(directory, args.limit)
    print(f"Found {len(file_pairs)} file pairs.")

    # Step 2: Get .aillyrc content
    print("Reading .aillyrc content...")
    aillyrc_content = get_aillyrc_content(directory)

    # Step 3: Convert to JSONL format
    print("Converting to JSONL format...")
    jsonl_entries = convert_to_jsonl_format(file_pairs, aillyrc_content)

    # Step 4: Write to output file
    print(f"Writing {len(jsonl_entries)} entries to {output_path}...")
    write_jsonl_file(jsonl_entries, output_path)

    print("Done!")


if __name__ == "__main__":
    main()
