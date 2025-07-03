import pytest
from typing import List

from aws_doc_sdk_examples_tools.lliam.domain.commands import CreatePrompts
from aws_doc_sdk_examples_tools.lliam.domain.model import Prompt
from aws_doc_sdk_examples_tools.lliam.service_layer.create_prompts import create_prompts
from aws_doc_sdk_examples_tools.lliam.service_layer.unit_of_work import AbstractUnitOfWork
from aws_doc_sdk_examples_tools.lliam.adapters.repository import (
    AbstractPromptRepository,
    AbstractDocGenRepository,
)


class FakePromptRepository(AbstractPromptRepository):
    def __init__(self):
        super().__init__()
        self.committed_prompts = {}
        self.system_prompts = {
            "system1.md": Prompt("system1.md", "System prompt 1 content"),
            "system2.md": Prompt("system2.md", "System prompt 2 content"),
        }
        self.partition_name = None

    def _add(self, prompt: Prompt):
        self.to_write[prompt.id] = prompt.content

    def _batch(self, prompts: List[Prompt]):
        for i, prompt in enumerate(prompts):
            batch_name = f"batch{(i // 150) + 1:03}"
            prompt.id = f"{batch_name}/{prompt.id}"
            self._add(prompt)

    def _commit(self):
        self.committed_prompts.update(self.to_write)
        self.to_write = {}

    def _get(self, id: str) -> Prompt:
        if id in self.system_prompts:
            return self.system_prompts[id]
        raise KeyError(f"Prompt {id} not found")

    def rollback(self):
        self.to_write = {}


class FakeDocGenRepository(AbstractDocGenRepository):
    def __init__(self):
        self.mock_prompts = [
            Prompt("example1.md", "Example 1 code content"),
            Prompt("example2.md", "Example 2 code content"),
        ]

    def _get_new_prompts(self, doc_gen_root: str) -> List[Prompt]:
        return self.mock_prompts

    def rollback(self):
        pass


class FakeUnitOfWork(AbstractUnitOfWork):
    def __init__(self):
        self.prompts = FakePromptRepository()
        self.doc_gen = FakeDocGenRepository()
        self.committed = False

    def _commit(self):
        self.committed = True
        self.prompts.commit()

    def rollback(self):
        self.committed = False
        self.prompts.rollback()
        self.doc_gen.rollback()


def test_create_prompts_writes_when_commit_called():
    """Test that create_prompts successfully writes prompts when commit is called."""
    uow = FakeUnitOfWork()
    cmd = CreatePrompts(
        doc_gen_root="/fake/doc_gen_root",
        system_prompts=["system1.md", "system2.md"],
        out_dir="/fake/output"
    )

    create_prompts(cmd, uow)

    # Ailly config should be in committed prompts
    assert ".aillyrc" in uow.prompts.committed_prompts
    ailly_config_content = uow.prompts.committed_prompts[".aillyrc"]
    assert "System prompt 1 content" in ailly_config_content
    assert "System prompt 2 content" in ailly_config_content
    
    # New prompts from DocGen should be in committed prompts
    assert "batch001/example1.md" in uow.prompts.committed_prompts
    assert "batch001/example2.md" in uow.prompts.committed_prompts
    assert uow.prompts.committed_prompts["batch001/example1.md"] == "Example 1 code content"
    assert uow.prompts.committed_prompts["batch001/example2.md"] == "Example 2 code content"