#!/usr/bin/env python

import logging
import os
from pathlib import Path
from typing import List
import yaml

from aws_doc_sdk_examples_tools.doc_gen import DocGen, Snippet

DEFAULT_METADATA_PREFIX = "[DEFAULT]"


# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def make_doc_gen(root: Path) -> DocGen:
    """Create and return a DocGen instance from the given root directory."""
    doc_gen = DocGen.from_root(root)
    doc_gen.collect_snippets()
    return doc_gen


def write_prompts(doc_gen: DocGen, out_dir: Path, language: str) -> None:
    examples = doc_gen.examples
    snippets = doc_gen.snippets
    for example_id, example in examples.items():
        # TCXContentAnalyzer prefixes new metadata title/title_abbrev entries with
        # the DEFAULT_METADATA_PREFIX. Checking this here to make sure we're only
        # running the LLM tool on new extractions.
        title = example.title or ""
        title_abbrev = example.title_abbrev or ""
        if title.startswith(DEFAULT_METADATA_PREFIX) and title_abbrev.startswith(
            DEFAULT_METADATA_PREFIX
        ):
            prompt_path = out_dir / f"{example_id}.md"
            snippet_key = (
                example.languages[language]
                .versions[0]
                .excerpts[0]
                .snippet_files[0]
                .replace("/", ".")
            )
            snippet = snippets[snippet_key]
            prompt_path.write_text(snippet.code, encoding="utf-8")


def setup_ailly(system_prompts: List[str], out_dir: Path) -> None:
    """Create the .aillyrc configuration file."""
    fence = "---"
    options = {
        "isolated": "true",
        "mcp": {
            "awslabs.aws-documentation-mcp-server": {
                "type": "stdio",
                "command": "uvx",
                "args": ["awslabs.aws-documentation-mcp-server@latest"],
            }
        },
    }
    options_block = yaml.dump(options).strip()
    prompts_block = "\n".join(system_prompts)

    content = f"{fence}\n{options_block}\n{fence}\n{prompts_block}"

    aillyrc_path = out_dir / ".aillyrc"
    aillyrc_path.write_text(content, encoding="utf-8")


def read_files(values: List[str]) -> List[str]:
    """Read contents of files into a list of file contents."""
    contents = []
    for value in values:
        if os.path.isfile(value):
            with open(value, "r", encoding="utf-8") as f:
                contents.append(f.read())
        else:
            contents.append(value)
    return contents


def validate_root_path(doc_gen_root: Path):
    assert doc_gen_root.is_dir()


def make_prompts(
    doc_gen_root: Path, system_prompts: List[str], out_dir: Path, language: str
) -> None:
    """Generate prompts and configuration files for Ailly."""
    validate_root_path(doc_gen_root)
    out_dir.mkdir(parents=True, exist_ok=True)
    system_prompts = read_files(system_prompts)
    setup_ailly(system_prompts, out_dir)
    doc_gen = make_doc_gen(doc_gen_root)
    write_prompts(doc_gen=doc_gen, out_dir=out_dir, language=language)
