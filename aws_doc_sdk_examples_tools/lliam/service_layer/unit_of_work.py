from aws_doc_sdk_examples_tools.fs import Fs, PathFs
from aws_doc_sdk_examples_tools.lliam.adapters.repository import (
    PromptRepository,
    DocGenRepository,
)


class FsUnitOfWork:
    def __init__(self, fs: Fs = PathFs()):
        self.fs = fs

    def __enter__(self):
        self.prompts = PromptRepository(fs=self.fs)
        self.doc_gen = DocGenRepository(fs=self.fs)

    def __exit__(self, *args):
        self.rollback()

    def commit(self):
        self.prompts.commit()

    def rollback(self):
        self.prompts.rollback()
        self.doc_gen.rollback()
