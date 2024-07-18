# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

import json
from argparse import ArgumentParser
from pathlib import Path
import logging

from .doc_gen import DocGen, DocGenEncoder
from .entities import EntityErrors

logging.basicConfig(level=logging.INFO)


def main():
    parser = ArgumentParser(description="Parse examples from example metadata.")
    parser.add_argument(
        "--from-root",
        action="extend",
        nargs="+",
        required=True,
        type=str,
        help="Generate from a path. Expects a path to a directory with a .doc_gen sub-directory.",
    )
    parser.add_argument(
        "--write-json",
        default="doc_gen.json",
        type=str,
        help="Output a JSON version of the computed DocGen with some properties stripped out. Includes any errors.",
    )

    parser.add_argument(
        "--strict",
        action="store_true",
        help="Exit with non-zero code if errors are present. By default errors are written to the output.",
    )

    parser.add_argument(
        "--skip-entity-expansion",
        action="store_true",
        help="Do not expand entities. Entities are expanded by default.",
    )

    args = parser.parse_args()

    merged_doc_gen = DocGen.empty()
    for root in args.from_root:
        unmerged_doc_gen = DocGen.from_root(Path(root))
        merged_doc_gen.merge(unmerged_doc_gen)

    if args.strict and merged_doc_gen.errors:
        logging.error("Errors found in metadata: %s", merged_doc_gen.errors)
        exit(1)

    if not args.skip_entity_expansion:
        # Replace entities
        for example in merged_doc_gen.examples.values():
            errors = EntityErrors()
            print(example)
            title, title_errors = merged_doc_gen.expand_entities(example.title)
            errors.extend(title_errors)

            title_abbrev, title_abbrev_errors = merged_doc_gen.expand_entities(
                example.title_abbrev
            )
            errors.extend(title_abbrev_errors)

            synopsis, synopsis_errors = merged_doc_gen.expand_entities(example.synopsis)
            errors.extend(synopsis_errors)

            synopsis_list = []
            for synopsis in example.synopsis_list:
                expanded_synopsis, synopsis_errors = merged_doc_gen.expand_entities(
                    synopsis
                )
                synopsis_list.append(expanded_synopsis)
                errors.extend(synopsis_errors)

            if errors:
                logging.error(
                    f"Errors expanding entities for example: {example}. {errors}"
                )
                exit(1)

            example.title = title
            example.title_abbrev = title_abbrev
            example.synopsis = synopsis
            example.synopsis_list = synopsis_list

    serialized = json.dumps(merged_doc_gen, cls=DocGenEncoder)

    with open(args.write_json, "w") as out:
        out.write(serialized)


if __name__ == "__main__":
    main()
