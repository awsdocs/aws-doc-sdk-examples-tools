from collections import Counter
from dataclasses import replace
import logging
from typing import Dict

from aws_doc_sdk_examples_tools.doc_gen import DocGen
from aws_doc_sdk_examples_tools.lliam.domain.commands import DedupeReservoir
from aws_doc_sdk_examples_tools.metadata import Example
from aws_doc_sdk_examples_tools.yaml_writer import prepare_write, write_many
from aws_doc_sdk_examples_tools.project_validator import ValidationConfig

logger = logging.getLogger(__name__)


def make_title_abbreviation(example: Example, counter: Counter):
    count = counter[example.title_abbrev]
    abbrev = f"{example.title_abbrev} ({count + 1})" if count else example.title_abbrev
    counter[example.title_abbrev] += 1
    return abbrev


def handle_dedupe_reservoir(cmd: DedupeReservoir, uow: None):
    doc_gen = DocGen.from_root(cmd.root, validation=ValidationConfig(check_aws=False))

    examples: Dict[str, Example] = {}

    for id, example in doc_gen.examples.items():
        if cmd.packages and example.file:
            package = example.file.name.split("_metadata.yaml")[0]
            if package in cmd.packages:
                examples[id] = example
        else:
            examples[id] = example

    title_abbrev_counts: Counter = Counter()

    for id, example in examples.items():
        examples[id] = replace(
            example,
            title_abbrev=make_title_abbreviation(example, title_abbrev_counts),
        )

    writes = prepare_write(examples)
    write_many(cmd.root, writes)
