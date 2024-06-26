# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

import json
from argparse import ArgumentParser
from pathlib import Path
from .doc_gen import DocGen, DocGenEncoder, DocGenDecoder


def doc_gen():
    parser = ArgumentParser(description="Parse examples from example metadata.")
    parser.add_argument(
        "--from-root",
        help="Generate from a path. Expects a path to a directory with a .doc_gen sub-directory.",
        action="extend",
        nargs="+",
        required=True,
        type=str
    )
    parser.add_argument(
       "--write-json",
       default="doc_gen.json",
       help="Output a JSON version of the computed DocGen."
    )
    args = parser.parse_args()

    merged_doc_gen = DocGen.empty()
    for root in args.from_root:
      unmerged_doc_gen = DocGen.from_root(Path(root))
      merged_doc_gen.merge(unmerged_doc_gen)

    serialized = json.dumps(merged_doc_gen, cls=DocGenEncoder)
    
    with open(args.write_json, "w") as out:
       out.write(serialized)
