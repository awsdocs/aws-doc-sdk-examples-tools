from argparse import ArgumentParser
from collections import defaultdict
from dataclasses import asdict
from pathlib import Path
from typing import Any, DefaultDict, Dict, List, Tuple

import logging
import yaml

from aws_doc_sdk_examples_tools.doc_gen import DocGen
from aws_doc_sdk_examples_tools.metadata import Example

logging.basicConfig(level=logging.INFO)

logger = logging.getLogger(Path(__file__).name)


def write_many(root: Path, to_write: Dict[str, str]):
    for path, examples in to_write.items():
        with open(root / path, "w") as file:
            file.write(examples)


def dump_yaml(value: Any) -> str:
    repr: str = yaml.dump(value, sort_keys=False, width=float("inf"))
    repr = repr.replace(r"!!set {}", r"{}")
    return repr


def prepare_write(examples: Dict[str, Example]) -> Dict[str, str]:
    reindexed: DefaultDict[Path, Dict[str, Any]] = defaultdict(dict)

    for id, example in examples.items():
        if example.file:
            reindexed[example.file][id] = example_dict(asdict(example))

    to_write = {str(path): dump_yaml(examples) for path, examples in reindexed.items()}

    return to_write


EXAMPLE_FIELD_ORDER = [
    # "id", # do not include ID, it goes in the key
    # "file", # similarly, do not include the file, it's the path to write to later
    "title",
    "title_abbrev",
    "synopsis",
    "synopsis_list",
    "guide_topic",
    # "doc_filenames", # These are currently generated, and don't need to be stored.
    "source_key",
    "category",
    "suppress_publish",
    "languages",
    "service_main",
    "services",
]

VERSION_FIELD_ORDER = [
    "sdk_version",
    "block_content",
    "github",
    "sdkguide",
    "more_info",
    "owner",
    "authors",
    "source",
    "excerpts",
]

EXCERPT_FIELD_ORDER = [
    "description",
    "genai",
    "snippet_tags",
    "snippet_files",
]


def reorder_dict(order: List[str], dict: Dict) -> Dict:
    replaced = {}

    for field in order:
        if value := dict[field]:
            replaced[field] = value

    return replaced


def example_dict(example: Dict) -> Dict:
    replaced = reorder_dict(EXAMPLE_FIELD_ORDER, example)

    replaced["languages"] = {
        k: dict(versions=[version_dict(version) for version in v["versions"]])
        for k, v in replaced["languages"].items()
    }

    return replaced


def version_dict(version: Dict) -> Dict:
    replaced = reorder_dict(VERSION_FIELD_ORDER, version)

    replaced["excerpts"] = [excerpt_dict(excerpt) for excerpt in replaced["excerpts"]]

    return replaced


def excerpt_dict(excerpt: Dict) -> Dict:
    reordered = reorder_dict(EXCERPT_FIELD_ORDER, excerpt)
    if reordered.get("genai") == "none":
        del reordered["genai"]
    return reordered


def collect_yaml(root: Path) -> Dict[str, Dict]:
    yaml_files: Dict[str, Dict] = {}
    metadata_dir = root / ".doc_gen" / "metadata"

    if not metadata_dir.exists():
        return yaml_files

    for yaml_path in metadata_dir.glob("**/*.yaml"):
        rel_path = yaml_path.relative_to(root)

        with open(yaml_path, "r") as file:
            try:
                content = yaml.safe_load(file)
                yaml_files[str(rel_path)] = content
            except yaml.YAMLError as e:
                logger.error(f"Error parsing YAML file {yaml_path}: {e}")

    return yaml_files


def report_yaml_differences(
    before_values: Dict[str, Dict], after_values: Dict[str, Dict]
) -> List[Tuple[str, str]]:
    differences = []
    for file_path in set(before_values.keys()) | set(after_values.keys()):
        before = before_values.get(file_path)
        after = after_values.get(file_path)

        if before != after:
            if file_path not in before_values:
                differences.append((file_path, "added"))
            elif file_path not in after_values:
                differences.append((file_path, "removed"))
            else:
                diff = f"{before}\n\n---\n\n{after}"
                differences.append((file_path, diff))

    return differences


def main():
    parser = ArgumentParser(
        description="Build a DocGen instance and normalize the metadata."
    )
    parser.add_argument("root", type=str, help="The root of a DocGen project")

    args = parser.parse_args()
    root = Path(args.root)

    if not root.is_dir():
        logger.error(f"Expected {root} to be a directory.")

    before_values = collect_yaml(root)
    doc_gen = DocGen.from_root(root)
    writes = prepare_write(doc_gen.examples)
    write_many(root, writes)
    after_values = collect_yaml(root)

    if before_values != after_values:
        differences = report_yaml_differences(before_values, after_values)
        logger.error(f"YAML content changed in {len(differences)} files after writing:")
        for difference in differences:
            logger.error(difference)
    else:
        logger.info(
            f"Metadata for {root.name} has been normalized and verified for consistency."
        )


if __name__ == "__main__":
    main()
