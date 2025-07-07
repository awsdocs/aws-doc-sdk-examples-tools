from pathlib import Path

from aws_doc_sdk_examples_tools.fs import Fs, RecordFs
from aws_doc_sdk_examples_tools.lliam.domain.commands import CreatePrompts
from aws_doc_sdk_examples_tools.lliam.service_layer.create_prompts import create_prompts
from aws_doc_sdk_examples_tools.lliam.service_layer.unit_of_work import AbstractUnitOfWork
from aws_doc_sdk_examples_tools.lliam.adapters.repository import (
    FsPromptRepository,
    FsDocGenRepository,
)


class FakeUnitOfWork(AbstractUnitOfWork):
    def __init__(self, fs: Fs):
        self.prompts = FsPromptRepository(fs=fs)
        self.doc_gen = FsDocGenRepository(fs=fs)
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
    fs = RecordFs({
        Path("system1.md"): "System prompt 1 content",
        Path("system2.md"): "System prompt 2 content",
        Path("fake/doc_gen_root"): ""
    })
    uow = FakeUnitOfWork(fs=fs)
    cmd = CreatePrompts(
        doc_gen_root="fake/doc_gen_root",
        system_prompts=["system1.md", "system2.md"],
        out_dir="/fake/output"
    )

    create_prompts(cmd, uow)

    # Ailly config should be in committed prompts
    ailly_config_path = Path("/fake/output/.aillyrc")
    assert fs.stat(ailly_config_path).exists
    ailly_config_content = fs.read(ailly_config_path)
    assert "System prompt 1 content" in ailly_config_content
    assert "System prompt 2 content" in ailly_config_content