from itertools import islice
from math import ceil, floor, log
from pathlib import Path
from typing import Any, Dict, Generator, Iterable, List, Tuple

from aws_doc_sdk_examples_tools.doc_gen import DocGen, Example
from aws_doc_sdk_examples_tools.fs import Fs, PathFs
from aws_doc_sdk_examples_tools.lliam.domain.model import Prompt
from aws_doc_sdk_examples_tools.lliam.config import BATCH_PREFIX

DEFAULT_METADATA_PREFIX = "DEFAULT"
DEFAULT_BATCH_SIZE = 150
IAM_POLICY_LANGUAGE = "IAMPolicyGrammar"


def batched(iterable: Iterable, n: int) -> Generator[Tuple, Any, None]:
    "Batch data into tuples of length n. The last batch may be shorter."
    # batched('ABCDEFG', 3) --> ABC DEF G
    if n < 1:
        raise ValueError("n must be at least one")
    it = iter(iterable)
    while batch := tuple(islice(it, n)):
        yield batch


class PromptRepository:
    to_write: Dict[str, str] = {}

    def __init__(self, fs: Fs = PathFs()):
        self.fs = fs

    def rollback(self):
        # TODO: This is not what rollback is for. We should be rolling back any
        # file changes
        self.to_write = {}

    def add(self, prompt: Prompt):
        self.to_write[prompt.id] = prompt.content

    def all_all(self, prompts: Iterable[Prompt]):
        for prompt in prompts:
            self.add(prompt)

    def batch(self, prompts: Iterable[Prompt]):
        prompt_list = list(prompts)

        if not prompt_list:
            return

        batches_count = ceil(len(prompt_list) / DEFAULT_BATCH_SIZE)
        padding = floor(log(batches_count, 10)) + 1
        for batch_num, batch in enumerate(batched(prompts, DEFAULT_BATCH_SIZE)):
            batch_name = f"{BATCH_PREFIX}{(batch_num + 1):0{padding}}"
            for prompt in batch:
                prompt.id = f"{batch_name}/{prompt.id}"
                self.add(prompt)

    def commit(self):
        base_path = Path(self.partition) if self.partition else Path(".")

        for id, content in self.to_write.items():
            if content:
                full_path = base_path / id
                self.fs.mkdir(full_path.parent)
                self.fs.write(full_path, content)

    def get(self, id: str):
        return Prompt(id, self.fs.read(Path(id)))

    def get_all(self, ids: List[str]) -> List[Prompt]:
        prompts = []
        for id in ids:
            prompt = self.get(id)
            prompts.append(prompt)
        return prompts

    def set_partition(self, name: str):
        self.partition_name = name

    @property
    def partition(self):
        return self.partition_name or ""


class DocGenRepository:
    def __init__(self, fs: Fs = PathFs()):
        self.fs = fs

    def rollback(self):
        # TODO: This is not what rollback is for. We should be rolling back any
        # file changes
        self._doc_gen = None

    def get_new_prompts(self, doc_gen_root: str) -> List[Prompt]:
        # Right now this is the only instance of DocGen used in this Repository,
        # but if that changes we need to move it up.
        self._doc_gen = DocGen.from_root(Path(doc_gen_root), fs=self.fs)
        self._doc_gen.collect_snippets()
        new_examples = self._get_new_examples()
        prompts = self._examples_to_prompts(new_examples)
        return prompts

    def _get_new_examples(self) -> List[Tuple[str, Example]]:
        examples = self._doc_gen.examples

        filtered_examples: List[Tuple[str, Example]] = []
        for example_id, example in examples.items():
            # TCXContentAnalyzer prefixes new metadata title/title_abbrev entries with
            # the DEFAULT_METADATA_PREFIX. Checking this here to make sure we're only
            # running the LLM tool on new extractions.
            title = example.title or ""
            title_abbrev = example.title_abbrev or ""
            if title.startswith(DEFAULT_METADATA_PREFIX) and title_abbrev.startswith(
                DEFAULT_METADATA_PREFIX
            ):
                filtered_examples.append((example_id, example))
        return filtered_examples

    def _examples_to_prompts(self, examples: List[Tuple[str, Example]]) -> List[Prompt]:
        snippets = self._doc_gen.snippets
        prompts = []
        for example_id, example in examples:
            key = (
                example.languages[IAM_POLICY_LANGUAGE]
                .versions[0]
                .excerpts[0]
                .snippet_files[0]
                .replace("/", ".")
            )
            snippet = snippets.get(key)
            prompts.append(Prompt(f"{example_id}.md", snippet.code))
        return prompts
