import json
import logging
from collections import Counter
from pathlib import Path
from typing import Dict, Iterable, List

from aws_doc_sdk_examples_tools.yaml_writer import prepare_write, write_many

from aws_doc_sdk_examples_tools.lliam.config import (
    AILLY_DIR_PATH,
    BATCH_PREFIX,
)
from aws_doc_sdk_examples_tools.lliam.domain.commands import UpdateReservoir
from aws_doc_sdk_examples_tools.doc_gen import DocGen, Example

logger = logging.getLogger(__name__)

IAM_LANGUAGE = "IAMPolicyGrammar"


def examples_from_updates(updates: List[Dict]) -> Iterable[Example]:
    """
    Takes a list of example metadata updates and returns an
    iterable of examples with the applied updates.
    """

    indexed_updates = {}
    for item in updates:
        if "id" in item:
            indexed_updates[item["id"]] = item

    examples = [
        Example(
            id=id,
            file=None,
            languages={},
            title=update.get("title"),
            title_abbrev=update.get("title_abbrev"),
            synopsis=update.get("synopsis"),
        )
        for id, update in indexed_updates.items()
    ]
    return examples


def make_title_abbreviation(old: Example, new: Example, abbreviations: Counter):
    language = old.languages[IAM_LANGUAGE]
    version = language.versions[0]
    source = version.source
    source_title = source.title if source else ""
    base = f"{new.title_abbrev} (from '{source_title}' docs)"
    abbreviations[base] += 1
    count = abbreviations[base]
    return f"{base} ({count})" if count > 1 else base


def update_examples(doc_gen: DocGen, examples: Iterable[Example]) -> Dict[str, Example]:
    """
    Merge a subset of example properties into a DocGen instance.
    """
    title_abbrevs = Counter(
        [example.title_abbrev for example in doc_gen.examples.values()]
    )
    updated = {}
    for example in examples:
        if doc_gen_example := doc_gen.examples.get(example.id):
            doc_gen_example.title = example.title
            doc_gen_example.title_abbrev = make_title_abbreviation(
                old=doc_gen_example, new=example, abbreviations=title_abbrevs
            )
            doc_gen_example.synopsis = example.synopsis
            updated[doc_gen_example.id] = doc_gen_example
        else:
            logger.warning(f"Could not find example with id: {example.id}")
    return updated


def update_doc_gen(doc_gen_root: Path, updates: List[Dict]) -> Dict[str, Example]:
    doc_gen = DocGen.from_root(doc_gen_root)
    examples = examples_from_updates(updates)
    updated_examples = update_examples(doc_gen, examples)
    return updated_examples


def handle_update_reservoir(cmd: UpdateReservoir, uow: None):
    update_files = (
        [AILLY_DIR_PATH / f"updates_{batch}.json" for batch in cmd.batches]
        if cmd.batches
        else list(AILLY_DIR_PATH.glob(f"updates_{BATCH_PREFIX}*.json"))
    )

    if not update_files:
        logger.warning("No IAM update files found to process")
        return

    for update_file in sorted(update_files):
        if update_file.exists():
            logger.info(f"Processing updates from {update_file.name}")
            updates = json.loads(update_file.read_text())
            if cmd.packages:
                updates = [
                    update
                    for package, update_list in updates.items()
                    if package in cmd.packages
                    for update in update_list
                ]
            if not updates:
                logger.warning(f"No matching updates to run in {update_file.name}")
                continue
            examples = update_doc_gen(doc_gen_root=cmd.root, updates=updates)

            writes = prepare_write(examples)
            write_many(cmd.root, writes)
        else:
            logger.warning(f"Update file not found: {update_file}")
