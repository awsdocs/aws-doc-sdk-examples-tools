# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

import argparse
from ast import literal_eval
from pathlib import Path
from sys import exit

from .doc_gen import DocGen
from .project_validator import check_files, verify_sample_files


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--root",
        default=f"{Path(__file__).parent.parent.parent}",
        help="The root path from which to search for files to check. The default is the root of the git repo (two up from this file).",
    )
    parser.add_argument(
        "--doc_gen_only",
        type=literal_eval,
        default=True,
        help="Only perform extended validation on snippet contents",
        required=False,
    )
    args = parser.parse_args()
    root_path = Path(args.root).resolve()

    doc_gen = DocGen.from_root(root=root_path)
    doc_gen.collect_snippets(snippets_root=root_path)
    doc_gen.validate()
    if not args.doc_gen_only:
        check_files(doc_gen.root, doc_gen.validation, doc_gen.errors)
        verify_sample_files(doc_gen.root, doc_gen.validation, doc_gen.errors)

    error_count = len(doc_gen.errors)
    if error_count > 0:
        print(f"{doc_gen.errors}")
        print(f"{error_count} errors found, please fix them.")
    else:
        print("All checks passed, you are cleared to check in.")

    return error_count


if __name__ == "__main__":
    exit(main())
