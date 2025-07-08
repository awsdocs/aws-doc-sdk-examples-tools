from aws_doc_sdk_examples_tools.fs import Fs
from aws_doc_sdk_examples_tools.lliam.adapters.repository import (
    FsPromptRepository,
    FsDocGenRepository,
)


class FsUnitOfWork:
    def __init__(self, fs: Fs):
        self.fs = fs

    def __enter__(self):
        self.prompts = FsPromptRepository(fs=self.fs)
        self.doc_gen = FsDocGenRepository(fs=self.fs)

    def __exit__(self, *args):
        self.rollback()

    def commit(self):
        self.prompts.commit()

    def collect_new_prompts(self):
        for prompt in self.prompts.seen:
            yield prompt

    def rollback(self):
        self.prompts.rollback()
        self.doc_gen.rollback()
