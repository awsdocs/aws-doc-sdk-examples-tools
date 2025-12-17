# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

import json
from argparse import ArgumentParser
from pathlib import Path
import logging

from .doc_gen import DocGen, DocGenEncoder

logging.basicConfig(level=logging.INFO)


def merge_roots(doc_gen: DocGen, roots: list[str]):
    for root in roots:
        unmerged_doc_gen = DocGen.from_root(Path(root))
        doc_gen.merge(unmerged_doc_gen)


def write_doc_gen(doc_gen: DocGen, json_out: str):
    serialized = json.dumps(doc_gen, cls=DocGenEncoder)

    with open(json_out, "w") as out:
        out.write(serialized)


def write_snippets(doc_gen: DocGen, roots: list[str], snippets_out: str):
    for root in roots:
        doc_gen.collect_snippets(Path(root))

    serialized_snippets = json.dumps(
        {
            "snippets": doc_gen.snippets,
            "snippet_files": doc_gen.snippet_files,
        },
        cls=DocGenEncoder,
    )
    with open(snippets_out, "w") as out:
        out.write(serialized_snippets)


def build_doc_gen(args):
    doc_gen = DocGen.empty()
    merge_roots(doc_gen, args.from_root)
    doc_gen.validate()
    doc_gen.fill_missing_fields()

    if not args.skip_entity_expansion:
        doc_gen.expand_entity_fields(doc_gen)

    if args.strict and doc_gen.errors:
        logging.error("Errors found in metadata: %s", doc_gen.errors)
        exit(1)

    if args.write_snippets:
        write_snippets(doc_gen, args.from_root, args.write_snippets)

    write_doc_gen(doc_gen, args.write_json)

    return doc_gen


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
        "--write-snippets",
        default="doc_gen_snippets.json",
        type=str,
        help="Output a JSON version of the computed DocGen with only snippets and snippet files. Separates snippet content from metadata content.",
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
    build_doc_gen(args)


if __name__ == "__main__":
    main()
