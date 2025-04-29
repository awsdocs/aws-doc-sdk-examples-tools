#!/usr/bin/env python

import argparse
import logging
import os
from pathlib import Path
from typing import Dict, List

from aws_doc_sdk_examples_tools.doc_gen import DocGen, Snippet

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def make_doc_gen(root: Path) -> DocGen:
    """Create and return a DocGen instance from the given root directory."""
    doc_gen = DocGen.from_root(root)
    doc_gen.collect_snippets()
    return doc_gen


def write_prompts(doc_gen: DocGen, out: Path) -> None:
    out.mkdir(parents=True, exist_ok=True)
    examples = doc_gen.examples
    snippets = doc_gen.snippets
    for example_id, example in examples.items():
        # Postfix with `.md` so Ailly will pick it up.
        prompt_path = out / f"{example_id}.md"
        # This assumes we're running DocGen specifically on AWSIAMPolicyExampleReservoir.
        snippet_key = example.languages["IAMPolicyGrammar"].versions[0].excerpts[0].snippet_files[0].replace("/", ".")
        snippet = snippets[snippet_key]
        prompt_path.write_text(snippet.code, encoding="utf-8")


def setup_ailly(system_prompts: List[str], out: Path) -> None:
    """Create the .aillyrc configuration file."""
    fence = "---"
    options = {"isolated": "true"}
    options_block = "\n".join(f"{key}: {value}" for key, value in options.items())
    prompts_block = "\n".join(system_prompts)

    content = f"{fence}\n{options_block}\n{fence}\n{prompts_block}"

    aillyrc_path = out / ".aillyrc"
    aillyrc_path.parent.mkdir(parents=True, exist_ok=True)
    aillyrc_path.write_text(content, encoding="utf-8")


def parse_prompts_arg(values: List[str]) -> List[str]:
    """Parse system prompts from a list of strings or file paths."""
    prompts = []
    for value in values:
        if os.path.isfile(value):
            with open(value, "r", encoding="utf-8") as f:
                prompts.append(f.read())
        else:
            prompts.append(value)
    return prompts


def main(
    doc_gen_root: Path, system_prompts: List[str], out: str = ".ailly_prompts"
) -> None:
    """Generate prompts and configuration files for Ailly."""
    out_path = Path(out)
    setup_ailly(system_prompts, out_path)

    doc_gen = make_doc_gen(doc_gen_root)
    write_prompts(doc_gen, out_path)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Write Ailly prompts for DocGen snippets and parse the results."
    )
    parser.add_argument(
        "--doc-gen-root", required=True, help="Path to a DocGen ready project."
    )
    parser.add_argument(
        "--system-prompts",
        nargs="+",
        required=True,
        help="List of prompt strings or file paths to store in a .aillyrc file.",
    )
    parser.add_argument(
        "--out",
        default=".ailly_prompts",
        help="Directory where Ailly prompt files will be written. Defaults to '.ailly_prompts'.",
    )

    args = parser.parse_args()

    doc_gen_root = Path(args.doc_gen_root)
    system_prompts = parse_prompts_arg(args.system_prompts)
    main(doc_gen_root, system_prompts, out=args.out)
