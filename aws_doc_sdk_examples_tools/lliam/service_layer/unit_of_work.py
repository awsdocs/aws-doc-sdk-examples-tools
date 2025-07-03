import abc

from aws_doc_sdk_examples_tools.lliam.adapters.repository import (
    AbstractPromptRepository,
    AbstractDocGenRepository,
    FsPromptRepository,
    FsDocGenRepository,
)


class AbstractUnitOfWork(abc.ABC):
    prompts: AbstractPromptRepository
    doc_gen: AbstractDocGenRepository

    def __enter__(self) -> "AbstractUnitOfWork":
        return self

    def __exit__(self, *args):
        self.rollback()

    def commit(self):
        self._commit()

    def collect_new_prompts(self):
        for prompt in self.prompts.seen:
            yield prompt

    @abc.abstractmethod
    def _commit(self):
        raise NotImplementedError

    @abc.abstractmethod
    def rollback(self):
        raise NotImplementedError


class FsUnitOfWork(AbstractUnitOfWork):

    def __enter__(self):
        self.prompts = FsPromptRepository()
        self.doc_gen = FsDocGenRepository()
        return super().__enter__()

    def __exit__(self, *args):
        super().__exit__(*args)

    def _commit(self):
        self.prompts.commit()

    def rollback(self):
        self.prompts.rollback()
        self.doc_gen.rollback()
