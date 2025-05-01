import argparse
import json
import logging
from pathlib import Path
from typing import Iterable

from aws_doc_sdk_examples_tools.doc_gen import DocGen, Example

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def examples_from_updates(updates_path: Path) -> Iterable[Example]:
    updates = json.loads(updates_path.read_text())
    examples = [
        Example(
            id=id,
            file=None,
            languages={},
            title=update.get("title"),
            title_abbrev=update.get("title_abbrev"),
            synopsis=update.get("synopsis"),
        )
        for id, update in updates.items()
    ]
    return examples


def update_examples(doc_gen: DocGen, examples: Iterable[Example]) -> None:
    for example in examples:
        if doc_gen_example := doc_gen.examples.get(example.id):
            doc_gen_example.title = example.title
            doc_gen_example.title_abbrev = example.title_abbrev
            doc_gen_example.synopsis = example.synopsis
        else:
            logger.warning(f"Could not find example with id: {example.id}")


def main(doc_gen_root: Path, updates_path: Path) -> None:
    doc_gen = DocGen.from_root(doc_gen_root)
    examples = examples_from_updates(updates_path)
    update_examples(doc_gen, examples)
    print(
        [
            {
                "title": ex.title,
                "title_abbrev": ex.title_abbrev,
                "synopsis": ex.synopsis,
            }
            for id, ex in doc_gen.examples.items()
        ]
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Apply a list of example updates to a doc gen instance"
    )
    parser.add_argument(
        "--doc-gen-root", required=True, help="Path to a DocGen ready project."
    )
    parser.add_argument(
        "--updates-path",
        default="example_updates.json",
        help="JSON file containing a list of example updates.",
    )

    args = parser.parse_args()

    doc_gen_root = Path(args.doc_gen_root)
    updates_path = Path(args.updates_path)
    main(doc_gen_root, updates_path)
