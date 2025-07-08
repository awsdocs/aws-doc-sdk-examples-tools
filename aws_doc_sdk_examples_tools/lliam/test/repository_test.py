from pathlib import Path

from aws_doc_sdk_examples_tools.fs import RecordFs
from aws_doc_sdk_examples_tools.lliam.adapters.repository import PromptRepository
from aws_doc_sdk_examples_tools.lliam.domain.model import Prompt


def test_batch_naming_occurs_properly():
    """Test that batch naming occurs properly when batching prompts."""
    fs = RecordFs({})
    repo = PromptRepository(fs=fs)

    prompts = []
    for i in range(300):
        prompts.append(Prompt(f"prompt_{i}.md", f"Content for prompt {i}"))

    repo.batch(prompts)

    expected_batch_1_prompts = 150
    expected_batch_2_prompts = 150

    batch_1_count = 0
    batch_2_count = 0
    for prompt_id in repo.to_write:
        if prompt_id.startswith("batch_1/"):
            batch_1_count += 1
        elif prompt_id.startswith("batch_2/"):
            batch_2_count += 1

    assert batch_1_count == expected_batch_1_prompts
    assert batch_2_count == expected_batch_2_prompts
