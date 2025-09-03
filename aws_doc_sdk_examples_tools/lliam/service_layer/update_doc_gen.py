from dataclasses import replace
import json
import logging
from pathlib import Path
from typing import Dict, Iterable, List, Sequence

from aws_doc_sdk_examples_tools.lliam.adapters.repository import DEFAULT_METADATA_PREFIX
from aws_doc_sdk_examples_tools.yaml_writer import prepare_write, write_many

from aws_doc_sdk_examples_tools.lliam.config import (
    AILLY_DIR_PATH,
    BATCH_PREFIX,
)
from aws_doc_sdk_examples_tools.lliam.domain.commands import UpdateReservoir
from aws_doc_sdk_examples_tools.lliam.domain.errors import (
    DomainError,
    CommandExecutionError,
)
from aws_doc_sdk_examples_tools.doc_gen import DocGen, Example

logger = logging.getLogger(__name__)

Updates = Dict[str, List[Dict[str, str]]]

IAM_LANGUAGE = "IAMPolicyGrammar"


def examples_from_updates(updates: Updates) -> Iterable[Example]:
    """
    Takes a list of example metadata updates and returns an
    iterable of examples with the applied updates.
    """

    indexed_updates = {}
    for update_list in updates.values():
        for item in update_list:
            if "id" in item:
                indexed_updates[item["id"]] = item

    examples = [
        Example(
            id=id,
            file=Path(),
            languages={},
            title=update.get("title"),
            title_abbrev=update.get("title_abbrev"),
            synopsis=update.get("synopsis"),
        )
        for id, update in indexed_updates.items()
    ]
    return examples


def get_source_title(example: Example) -> str:
    language = example.languages[IAM_LANGUAGE]
    version = language.versions[0]
    source = version.source
    return source.title if source else ""


def update_examples(doc_gen: DocGen, examples: Iterable[Example]) -> Dict[str, Example]:
    """
    Merge a subset of example properties into a DocGen instance.
    """

    for example in examples:
        if example.id in doc_gen.examples:
            source_title = get_source_title(doc_gen.examples[example.id])
            # This is a hack. TCA is replacing AWS with &AWS;, which entity converter
            # then does another pass on. So we end up with things like "&AWS; &GLUlong;"
            # which render as "AWS AWS Glue". We should look at this closer when time permits.
            source_title = source_title.replace("&AWS;", "AWS")
            new_abbrev = f"{example.title_abbrev} (from '{source_title}' guide)"
            doc_gen_example = replace(
                doc_gen.examples[example.id],
                title=example.title,
                title_abbrev=new_abbrev,
                synopsis=example.synopsis,
            )
            doc_gen.examples[example.id] = doc_gen_example
        else:
            logger.warning(f"Could not find example with id: {example.id}")
    return doc_gen.examples


def update_doc_gen(doc_gen: DocGen, updates: Updates) -> Dict[str, Example]:
    examples = examples_from_updates(updates)
    updated_examples = update_examples(doc_gen, examples)
    return updated_examples


def merge_updates(a: Updates, b: Updates) -> Updates:
    merged: Updates = dict(a)
    for package_name, updates in b.items():
        if package_name not in merged:
            merged[package_name] = updates
        else:
            # Assumption: Updates will not conflict.
            merged[package_name].extend(updates)
    return merged


def handle_update_reservoir(cmd: UpdateReservoir, uow: None) -> Sequence[DomainError]:
    update_files = (
        [AILLY_DIR_PATH / f"updates_{batch}.json" for batch in cmd.batches]
        if cmd.batches
        else list(AILLY_DIR_PATH.glob(f"updates_{BATCH_PREFIX}*.json"))
    )

    if not update_files:
        logger.warning("No IAM update files found to process")
        return []

    doc_gen = DocGen.from_root(cmd.root)

    combined_updates: Updates = {}

    for update_file in sorted(update_files):
        if update_file.exists():
            updates: Updates = json.loads(update_file.read_text())
            if cmd.packages:
                updates = {
                    package_name: update_list
                    for package_name, update_list in updates.items()
                    if package_name in cmd.packages
                }

            if not updates:
                logger.warning(f"No matching updates to run in {update_file.name}")
                continue

            combined_updates = merge_updates(combined_updates, updates)

        else:
            logger.warning(f"Update file not found: {update_file}")

    updated_examples = update_doc_gen(doc_gen=doc_gen, updates=combined_updates)
    writes = prepare_write(updated_examples)
    write_many(cmd.root, writes)
    # TODO Catch and return any errors
    return []
