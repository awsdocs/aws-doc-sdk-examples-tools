from typing import List

from aws_doc_sdk_examples_tools.doc_gen import Example, Snippet


class Prompt:
    def __init__(self, id: str, content: str):
        self.id = id
        self.content = content


class Policies:
    def __init__(self, examples: List[Example], snippets: List[Snippet]):
        self.examples = examples
        self.snippets = snippets
