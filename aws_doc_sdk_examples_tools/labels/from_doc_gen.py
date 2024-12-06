from typing import Dict, Iterable, List, Set

from aws_doc_sdk_examples_tools.doc_gen import DocGen
from aws_doc_sdk_examples_tools.metadata import Example as DocGenExample
from aws_doc_sdk_examples_tools.snippets import Snippet as DocGenSnippet
from aws_doc_sdk_examples_tools.sdks import Sdk as DocGenSdk
from aws_doc_sdk_examples_tools.services import Service as DocGenService

from .labels import Sdk, Service, Example, Snippet, Expanded, Label, Excerpt
from . import known_labels


def from_doc_gen(doc_gen: DocGen):
    sdks: Set[Sdk] = _sdks(doc_gen.sdks)
    services: Set[Service] = _services(doc_gen.services)
    snippets: Set[Snippet] = _snippets(doc_gen.examples.values(), doc_gen.snippets)
    examples: Set[Example] = _examples(doc_gen.examples)

    return dict(
        sdks=frozenset(sdks),
        services=frozenset(services),
        snippets=frozenset(snippets),
        examples=frozenset(examples),
    )


def _sdks(doc_gen_sdks: Dict[str, DocGenSdk]) -> Set[Sdk]:
    sdks: Set[Sdk] = set()
    for id, sdk in doc_gen_sdks.items():
        for v in _sdk(id, sdk):
            sdks.add(v)
    return sdks


def _sdk(id: str, doc_gen_sdk: DocGenSdk) -> Iterable[Sdk]:
    for v in doc_gen_sdk.versions:
        labels: List[Label] = []
        if v.caveat:
            labels.append(Label(name="caveat", value=v.caveat))
        sdk = Sdk(
            language=doc_gen_sdk.property,
            version=str(v.version),
            name=Expanded(long=v.long, short=v.short),
            labels=labels
        )
        yield sdk


def _services(doc_gen_services: Dict[str, DocGenService]) -> Set[Service]:
    return set([_service(id, service) for id, service in doc_gen_services.items()])


def _service(id: str, doc_gen_service: DocGenService) -> Service :
    labels: List[Label] = []
    if doc_gen_service.caveat:
        labels.append(Label(name=known_labels.CAVEAT, value=doc_gen_service.caveat))

    expanded = Expanded(long="", short="")
    if doc_gen_service.expanded:
        expanded = Expanded(long=doc_gen_service.expanded.long, short=doc_gen_service.expanded.short)

    service = Service(
        id=id,
        sort=doc_gen_service.sort,
        name=Expanded(long=doc_gen_service.long, short=doc_gen_service.short),
        expanded=expanded,
        version=str(doc_gen_service.version),
        labels=labels,
    )
    return service


def _examples(examples: Dict[str, DocGenExample]) -> Set[Example]:
    return set([_example(id, example) for id, example in examples.items()])


def _example(id: str, doc_gen_example: DocGenExample) -> Example:
    labels = doc_gen_example_labels(doc_gen_example)

    example = Example(
        id=id,
        title=doc_gen_example.title,
        title_abbrev=doc_gen_example.title_abbrev,
        synopsis=doc_gen_example.synopsis or "",
        synopsis_list=doc_gen_example.synopsis_list,
        labels=labels,
    )

    return example


def doc_gen_example_labels(doc_gen_example):
    labels: List[Label] = []
    if doc_gen_example.category:
        labels.append(Label(name=known_labels.CATEGORY, value=doc_gen_example.category))
    if doc_gen_example.service_main:
        labels.append(Label(name=known_labels.SERVICE, value=doc_gen_example.service_main))
    for service, actions in doc_gen_example.services.items():
        labels.append(Label(name=known_labels.SERVICE, value=service))
        for action in actions:
            labels.append(Label(name=known_labels.ACTION, value=action))
    return labels


def _snippets(doc_gen_examples: Iterable[DocGenExample], doc_gen_snippets: Dict[str, DocGenSnippet]) -> Set[Snippet]:
    snippets = set()
    for example in doc_gen_examples:
        example_labels = doc_gen_example_labels(example)
        for lang, language in example.languages.items():
            lang = lang.lower()
            for version in language.versions:
                excerpts: List[Excerpt] = []
                if version.block_content:
                    excerpts.append(Excerpt(description=version.block_content))
                for excerpt in version.excerpts:
                    if excerpt.description:
                        excerpts.append(Excerpt(description=excerpt.description))
                    for tag in [*excerpt.snippet_tags, *excerpt.snippet_files]:
                        doc_gen_snippet = doc_gen_snippets.get(tag, None)
                        if doc_gen_snippet:
                            excerpts.append(Excerpt(path=doc_gen_snippet.file, range=(doc_gen_snippet.line_start, doc_gen_snippet.line_end), content=doc_gen_snippet.code))
                labels: List[Label] = [
                    *example_labels,
                    Label(name=known_labels.SDK, value=f"{lang}:{version.sdk_version}"),
                ]
                for service in version.add_services:
                    labels.append(Label(name=known_labels.SERVICE, value=service))
                snippet = Snippet(
                    id=f"{example.id}:{lang}:{version.sdk_version}",
                    labels=labels,
                    excerpts=excerpts
                )
                snippets.add(snippet)

    return snippets
