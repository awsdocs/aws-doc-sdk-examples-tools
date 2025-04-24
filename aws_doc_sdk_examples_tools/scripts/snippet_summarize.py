#!/usr/bin/env python

import argparse
import json
import logging
import os
from pathlib import Path
from typing import Dict, Optional 

import boto3
from botocore.exceptions import ClientError

from aws_doc_sdk_examples_tools.doc_gen import DocGen, Snippet
from aws_doc_sdk_examples_tools.scripts.retry import retry_with_backoff


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class BedrockRuntime:
    def __init__(self, model_id: str = "us.anthropic.claude-3-7-sonnet-20250219-v1:0"):
        self.client = boto3.client("bedrock-runtime")
        self.model_id = model_id
        self.base_prompt = Path(
            os.path.dirname(__file__), "base_prompt.txt"
        ).read_text()
        self.conversation = [{"role": "user", "content": [{"text": self.base_prompt}]}]

    def converse(self, conversation):
        self.conversation.extend(conversation)
        response = self.client.converse(
            modelId=self.model_id,
            messages=self.conversation,
            inferenceConfig={"maxTokens": 512, "temperature": 0.5, "topP": 0.9},
        )
        response_text = response["output"]["message"]["content"][0]["text"]
        return response_text


def make_doc_gen(root: Path):
    doc_gen = DocGen.from_root(root)
    doc_gen.collect_snippets()
    return doc_gen


@retry_with_backoff(exceptions=(ClientError,), max_retries=10)
def generate_snippet_description(
    bedrock_runtime: BedrockRuntime, snippet: Snippet, prompt: Optional[str]
) -> Dict:
    content = (
        [{"text": prompt}, {"text": snippet.code}]
        if prompt
        else [{"text": snippet.code}]
    )
    conversation = [
        {
            "role": "user",
            "content": content,
        }
    ]

    response_text = bedrock_runtime.converse(conversation)

    try:
        # This assumes the response is JSON, which couples snippet
        # description generation to a specific prompt.
        return json.loads(response_text)
    except Exception as e:
        logger.warning(f"Failed to parse response. Response: {response_text}")
        return {}


def generate_descriptions(snippets: Dict[str, Snippet], prompt: Optional[str]):
    runtime = BedrockRuntime()
    results = []
    for snippet_id, snippet in snippets.items():
        response = generate_snippet_description(runtime, snippet, prompt)
        results.append(response)
        # Just need a few results for the demo.
        if len(results) == 3:
            break
    print(results)


def main(doc_gen_root: Path, prompt: Optional[Path]):
    doc_gen = make_doc_gen(doc_gen_root)
    prompt_text = prompt.read_text() if prompt and prompt.exists() else None
    generate_descriptions(doc_gen.snippets, prompt_text)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Generate new titles and descriptions for DocGen snippets"
    )
    parser.add_argument(
        "--doc-gen-root", required=True, help="Path to DocGen ready project"
    )
    parser.add_argument(
        "--prompt",
        help="Path to an additional prompt to be used for refining the output",
    )
    args = parser.parse_args()

    doc_gen_root = Path(args.doc_gen_root)
    prompt = Path(args.prompt) if args.prompt else None
    main(doc_gen_root, prompt)
