import logging
import re

from collections import Counter
from dataclasses import replace
from pathlib import Path
from typing import Dict, Iterable, List

from aws_doc_sdk_examples_tools.doc_gen import DocGen
from aws_doc_sdk_examples_tools.lliam.domain.commands import DedupeReservoir
from aws_doc_sdk_examples_tools.metadata import Example
from aws_doc_sdk_examples_tools.yaml_writer import prepare_write, write_many
from aws_doc_sdk_examples_tools.project_validator import ValidationConfig

logger = logging.getLogger(__name__)


def make_abbrev(example: Example, counter: Counter) -> str:
    if not example.title_abbrev:
        return ""

    count = counter[example.title_abbrev]
    abbrev = f"{example.title_abbrev} ({count + 1})" if count else example.title_abbrev
    counter[example.title_abbrev] += 1
    return abbrev


def reset_abbrev_count(examples: Dict[str, Example]) -> Dict[str, Example]:
    """
    Reset all duplicate title abbreviations back to their un-enumerated state.

    I don't love this. Ideally we would only update new title_abbrev fields
    with the incremented count. But there's no way to know which ones are new
    or even which particular title_abbrev is the original.

    Ex.
    title_abbrev: some policy
    title_abbrev: some policy (2)
    title_abbrev: some policy
    title_abbrev: some policy

    Which one is the original? Which ones are new?
    """

    updated_examples = {}

    for id, example in examples.items():
        updated_examples[id] = replace(
            example,
            title_abbrev=re.sub(r"(\s\(\d+\))*$", "", example.title_abbrev or ""),
        )

    return updated_examples


def example_in_packages(example: Example, packages: List[str]) -> bool:
    if packages and example.file:
        example_pkg_name = example.file.name.split("_metadata.yaml")[0]
        if not example_pkg_name in packages:
            return False
    return True


def dedupe_examples(
    examples: Dict[str, Example], packages: List[str]
) -> Dict[str, Example]:
    filtered = {
        id: ex for id, ex in examples.items() if example_in_packages(ex, packages)
    }

    reset_examples = reset_abbrev_count(filtered)

    counter: Counter = Counter()

    return {
        id: replace(ex, title_abbrev=make_abbrev(ex, counter))
        for id, ex in reset_examples.items()
    }


def write_examples(examples: Dict[str, Example], root: Path):
    writes = prepare_write(examples)
    write_many(root, writes)


def handle_dedupe_reservoir(cmd: DedupeReservoir, uow: None):
    doc_gen = DocGen.from_root(cmd.root, validation=ValidationConfig(check_aws=False))
    examples = dedupe_examples(doc_gen.examples, cmd.packages)
    write_examples(examples, cmd.root)
