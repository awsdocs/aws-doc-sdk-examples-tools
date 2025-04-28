import argparse
import json
import logging
from pathlib import Path
from typing import List, Dict, Optional

logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)


def extract_json_from_text(text: str) -> Optional[Dict]:
    brace_stack: List[str] = []
    json_start = None

    for i, char in enumerate(text):
        if char == "{":
            if not brace_stack:
                json_start = i
            brace_stack.append(char)
        elif char == "}":
            if brace_stack:
                brace_stack.pop()
                if not brace_stack and json_start is not None:
                    json_candidate = text[json_start : i + 1]
                    try:
                        return json.loads(json_candidate)
                    except json.JSONDecodeError:
                        logger.warning(
                            "Found a brace-balanced block, but it isn't valid JSON."
                        )
                        # Continue searching
    return None


def process_files(file_paths: List[str]) -> List[Dict]:
    results = []
    for path in file_paths:
        try:
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
            json_data = extract_json_from_text(content)
            if json_data is not None:
                results.append(json_data)
            else:
                logger.warning(f"No valid JSON object found in file: {f.name}")
        except Exception as e:
            logger.warning(f"Error processing file {path}: {e}")
    return results


def write_objects(object: Dict, out: Path):
    out.write_text(json.dumps(object, indent=2))


def main():
    parser = argparse.ArgumentParser(
        description="Extract JSON objects from one or more text files."
    )

    parser.add_argument("files", nargs="+", help="List of files to process")

    parser.add_argument(
        "--out",
        default="out.json",
        help="File path where the resultant json will be written.",
    )

    args = parser.parse_args()

    json_objects = process_files(args.files)
    out = Path(args.out)
    write_objects(json_objects, out)


if __name__ == "__main__":
    main()
