#!/usr/bin/env python3
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any, Dict, Literal, List, Optional, Set, Union, Iterable
from os.path import splitext
from pathlib import Path

from . import metadata_errors
from .metadata_errors import (
    MetadataErrors,
    MetadataParseError,
    DuplicateItemException,
    ExampleMergeMismatchedId,
    ExampleMergeMismatchedLanguage,
    ExampleMergeConflict,
)
from .metadata_validator import StringExtension
from .project_validator import ValidationConfig
from .services import Service
from .sdks import Sdk


@dataclass
class Url:
    title: str
    url: Optional[str]

    @classmethod
    def from_yaml(
        cls, yaml: None | Dict[str, Optional[str]]
    ) -> Optional[Union[Url, MetadataParseError]]:
        if yaml is None:
            return None
        title = yaml.get("title", "")
        url = yaml.get("url", "")

        if title is None:
            return metadata_errors.URLMissingTitle(url=str(url))

        return cls(title, url)


@dataclass
class Excerpt:
    description: Optional[str]
    # Tags embedded in source files to extract as snippets.
    snippet_tags: List[str]
    # A path within the repo to extract the entire file as a snippet.
    snippet_files: List[str] = field(default_factory=list)
    # The amount to which generative AI was used to create this content.
    #
    # none: No GenAI generated content is included in this excerpt, but it may have been consulted for reference.
    # some: A human wrote this content, though some portions may be copied or inserted from a GenAI tool.
    # most: The bulk of this content was written by a GenAI tool, though a human has edited and reviewed it for accuracy.
    # all: This content was entirely written by GenAI, and has not been reviewed by a human.
    genai: Literal["none", "some", "most", "all"] = "none"

    @classmethod
    def from_yaml(cls, yaml: Any) -> tuple["Excerpt", MetadataErrors]:
        description = yaml.get("description")
        snippet_files = [str(file) for file in yaml.get("snippet_files", [])]
        snippet_tags = [str(tag) for tag in yaml.get("snippet_tags", [])]
        genai = yaml.get("genai", "none")

        errors = MetadataErrors()
        if genai not in {"none", "some", "most", "all"}:
            errors.append(metadata_errors.FieldError(field="genai", value=genai))

        return (cls(description, snippet_tags, snippet_files, genai), errors)


@dataclass
class Version:
    sdk_version: int
    # Additional ZonBook XML to include in the tab for this sample.
    block_content: Optional[str] = field(default=None)
    # The specific code samples to include in the example.
    excerpts: List[Excerpt] = field(default_factory=list)
    # Link to the source code for this example. TODO rename.
    github: Optional[str] = field(default=None)
    add_services: Dict[str, Set[str]] = field(default_factory=dict)
    # Deprecated. Replace with guide_topic list.
    sdkguide: Optional[str] = field(default=None)
    # Link to additional topic places.
    more_info: List[Url] = field(default_factory=list)

    @classmethod
    def from_yaml(
        cls,
        yaml: Dict[str, Any],
        services: Dict[str, Service],
        cross_content_blocks: Set[str],
        is_action: bool,
        root: Path,
    ) -> tuple["Version", MetadataErrors]:
        errors = MetadataErrors()

        sdk_version = int(yaml.get("sdk_version", 0))
        if sdk_version == 0:
            errors.append(metadata_errors.MissingField(field="sdk_version"))

        block_content = yaml.get("block_content")
        github = yaml.get("github")
        sdkguide = yaml.get("sdkguide")

        if sdkguide is not None:
            if sdkguide.startswith("https://docs.aws.amazon.com"):
                errors.append(metadata_errors.InvalidSdkGuideStart(guide=sdkguide))

        if github is not None:
            _, ext = splitext(github)
            if ext != "":
                errors.append(
                    metadata_errors.InvalidGithubLink(
                        link=github, sdk_version=sdk_version
                    )
                )
            elif github.startswith("http"):
                pass  # Tributaries specify full GitHub path. Consider passing in GitHub root from tributaries and doing a full check at some point.
            elif not (root / github).exists():
                errors.append(
                    metadata_errors.MissingGithubLink(
                        link=github, sdk_version=sdk_version, root=root
                    )
                )

        excerpts = []
        for excerpt in yaml.get("excerpts", []):
            parsed, parse_errors = Excerpt.from_yaml(excerpt)
            excerpts.append(parsed)
            errors.extend(parse_errors)

        if len(excerpts) == 0 and block_content is None:
            errors.append(metadata_errors.MissingBlockContentAndExcerpt())
            excerpts = []
        if len(excerpts) > 0 and block_content is not None:
            errors.append(metadata_errors.BlockContentAndExcerptConflict())

        more_info: List[Url] = []
        for url in yaml.get("more_info", []):
            url = Url.from_yaml(url)
            if isinstance(url, Url):
                more_info.append(url)
            elif url is not None:
                errors.append(url)

        add_services = parse_services(yaml.get("add_services", {}), errors, services)
        if add_services and is_action:
            errors.append(metadata_errors.APIExampleCannotAddService())

        if block_content is not None and block_content not in cross_content_blocks:
            errors.append(metadata_errors.MissingCrossContent(block=block_content))

        for error in errors:
            if hasattr(error, "sdk_version"):
                error.sdk_version = sdk_version

        return (
            cls(
                sdk_version,
                block_content,
                excerpts,
                github,
                add_services,
                sdkguide,
                more_info,
            ),
            errors,
        )


@dataclass
class Language:
    name: str
    # A downcased, special-character-free version of the name. Matches a key of the same name in sdks.yaml.
    property: str
    versions: List[Version]

    def merge(self, other: "Language", errors: MetadataErrors):
        """Add new versions from `other`"""
        if self.name != other.name:
            errors.append(
                ExampleMergeMismatchedLanguage(
                    language=self.name, other_lang=other.name
                )
            )
            return
        self_versions = {v.sdk_version for v in self.versions}
        for other_version in other.versions:
            if other_version.sdk_version in self_versions:
                errors.append(
                    ExampleMergeConflict(
                        language=self.name, sdk_version=other_version.sdk_version
                    )
                )
            else:
                self.versions.append(other_version)
            # Merge down to the SDK Version level, so later guides can add new
            # excerpts to existing examples, but don't try to merge the excerpts
            # within the language. If a tributary or writer feels they need to
            # modify an excerpt, they should go modify the excerpt directly.

    @classmethod
    def from_yaml(
        cls,
        name: str,
        yaml: Any,
        sdks: Dict[str, Sdk],
        services: Dict[str, Service],
        blocks: Set[str],
        is_action: bool,
        root: Path,
    ) -> tuple[Language, MetadataErrors]:
        errors = MetadataErrors()
        if name not in sdks:
            errors.append(metadata_errors.UnknownLanguage(language=name))

        sdk = sdks.get(name)
        property = sdk.property if sdk else ""

        yaml_versions: List[Dict[str, Any]] | None = yaml.get("versions")
        if yaml_versions is None or len(yaml_versions) == 0:
            errors.append(metadata_errors.MissingField(field="versions"))
            yaml_versions = []

        versions: List[Version] = []
        for version in yaml_versions:
            vers, version_errors = Version.from_yaml(
                version, services, blocks, is_action, root
            )
            errors.extend(version_errors)
            versions.append(vers)

        for error in errors:
            if isinstance(error, MetadataParseError):
                error.language = name

        return cls(name, property, versions), errors


@dataclass
class Example:
    id: str
    file: Optional[Path]
    languages: Dict[str, Language]
    # Human readable title. TODO: Defaults to slug-to-title of the ID if not provided.
    title: Optional[str] = field(default="")
    # Used in the TOC. TODO: Defaults to slug-to-title of the ID if not provided.
    title_abbrev: Optional[str] = field(default="")
    synopsis: Optional[str] = field(default="")
    # String label categories. Categories inferred by cross-service with multiple services, and can be whatever else it wants. Controls where in the TOC it appears.
    category: Optional[str] = field(default=None)
    # Link to additional topic places.
    guide_topic: Optional[Url] = field(default=None)  # TODO: Url|List[Url]
    # TODO how to add a language here and require it in services_schema.
    # TODO document service_main and services. Not to be used by tributaries. Part of Cross Service.
    # List of services used by the examples. Lines up with those in services.yaml.
    service_main: Optional[str] = field(default=None)
    services: Dict[str, Set[str]] = field(default_factory=dict)
    # HTML file names corresponding to the documentation pages in the Code Library
    doc_filenames: Optional[DocFilenames] = field(default=None)
    synopsis_list: List[str] = field(default_factory=list)
    source_key: Optional[str] = field(default=None)

    def merge(self, other: Example, errors: MetadataErrors):
        """Combine `other` Example into self example.

        Merge down to the SDK Version level, so later guides can add new excerpts to existing examples, but don't try to merge the excerpts within the language.
        If a tributary or writer feels they need to modify an excerpt, they should go modify the excerpt directly.

        Keep title, title_abbrev, synopsis, guide_topic, category, service_main, synopsis_list, and source_key from source (typically awsdocs/aws-doc-sdk-examples).
        !NOTE: This means `merge` is NOT associative!

        Add error if IDs are not the same and return early.
        """
        if self.id != other.id:
            errors.append(
                ExampleMergeMismatchedId(
                    id=self.id, other_id=other.id, file=self.file, other_file=other.file
                )
            )
            return

        for service, actions in other.services.items():
            if service not in self.services:
                self.services[service] = actions

        for name, language in other.languages.items():
            if name not in self.languages:
                self.languages[name] = language
            else:
                merge_errs = MetadataErrors()
                self.languages[name].merge(language, merge_errs)
                for err in merge_errs:
                    err.id = self.id
                    err.file = self.file
                    if hasattr(err, "other_file"):
                        err.other_file = other.file
                errors.extend(merge_errs)

    @classmethod
    def from_yaml(
        cls,
        yaml: Any,
        sdks: Dict[str, Sdk],
        services: Dict[str, Service],
        blocks: Set[str],
        validation: ValidationConfig,
        root: Path,
    ) -> tuple[Example, MetadataErrors]:
        errors = MetadataErrors()

        title = get_with_valid_entities("title", yaml, errors, True)
        title_abbrev = get_with_valid_entities("title_abbrev", yaml, errors, True)
        synopsis = get_with_valid_entities("synopsis", yaml, errors, opt=True)
        synopsis_list = [str(syn) for syn in yaml.get("synopsis_list", [])]

        source_key = yaml.get("source_key")
        guide_topic = Url.from_yaml(yaml.get("guide_topic"))
        if isinstance(guide_topic, MetadataParseError):
            errors.append(guide_topic)
            guide_topic = None

        parsed_services = parse_services(yaml.get("services", {}), errors, services)
        category = yaml.get("category", "")
        if category == "":
            category = "Api" if len(parsed_services) == 1 else "Cross"
        is_action = category == "Api"
        is_basics = category == "Basics"

        if is_action:
            svc_actions = []
            for svc, actions in parsed_services.items():
                for action in actions:
                    svc_actions.append(f"{svc}:{action}")
            if len(svc_actions) != 1:
                errors.append(
                    metadata_errors.APIMustHaveOneServiceOneAction(
                        svc_actions=", ".join(svc_actions)
                    )
                )

        if validation.strict_titles:
            if is_action:
                if title or title_abbrev or synopsis or synopsis_list:
                    errors.append(metadata_errors.APICannotHaveTitleFields())
            elif is_basics:
                # Basics examples can have custom titles or no titles (in this case they're generated).
                if not (synopsis or synopsis_list):
                    errors.append(metadata_errors.BasicsMustHaveSynopsisField())
            else:
                if not (title and title_abbrev and (synopsis or synopsis_list)):
                    errors.append(metadata_errors.NonAPIMustHaveTitleFields())

        service_main = yaml.get("service_main", None)
        if service_main is not None and service_main not in services:
            try:
                errors.append(metadata_errors.UnknownService(service=service_main))
            except DuplicateItemException:
                pass

        yaml_languages = yaml.get("languages")
        languages: Dict[str, Language] = {}
        if yaml_languages is None:
            errors.append(metadata_errors.MissingField(field="languages"))
        else:
            for name in yaml_languages:
                language, errs = Language.from_yaml(
                    name, yaml_languages[name], sdks, services, blocks, is_action, root
                )
                languages[language.name] = language
                errors.extend(errs)

        return (
            cls(
                id="",
                file=None,
                title=title,
                title_abbrev=title_abbrev,
                category=category,
                guide_topic=guide_topic,
                languages=languages,
                service_main=service_main,
                services=parsed_services,
                synopsis=synopsis,
                synopsis_list=synopsis_list,
                source_key=source_key,
            ),
            errors,
        )


def parse_services(
    yaml: Any, errors: MetadataErrors, known_services: Dict[str, Service]
) -> Dict[str, Set[str]]:
    if yaml is None:
        return {}
    services: Dict[str, Set[str]] = {}
    for name in yaml:
        if name not in known_services:
            errors.append(metadata_errors.UnknownService(service=name))
        else:
            service: Dict[str, None] | Set[str] | None = yaml.get(name)
            # While .get replaces missing with {}, `sqs: ` in yaml parses a literal `None`
            if service is None:
                service = set()
            if isinstance(service, dict):
                service = set(service.keys())
            if isinstance(service, set):
                # Make a copy of the set for ourselves
                service = set(service)
            services[name] = set(service)
    return services


ALLOWED = ["&AWS;", "&AWS-Region;", "&AWS-Regions;" "AWSJavaScriptSDK"]


@dataclass
class CrossServicePage:
    cross: str


@dataclass
class SDKPageVersion:
    """
    A mapping of example type to a dictionary of service id's
    and their documentation URL. Cross service example have a
    special service id named `cross`.
    """

    actions_scenarios: Optional[Dict[str, str]] = None
    cross_service: Optional[CrossServicePage] = None


SDKPageLanguage = Dict[int, SDKPageVersion]
SDKPages = Dict[str, SDKPageLanguage]

ServicePages = Dict[str, str]


@dataclass
class DocFilenames:
    """
    Names that match the one or more Code Library entries for a single example.

    Example structure:
    ```
    transcribe_app.doc_filenames == {
        "service_pages": {
            "cognito-identity": "https://docs.aws.amazon.com/code-library/latest/ug/cognito-identity_example_cross_TranscriptionApp_section.html",
            "transcribe": "https://docs.aws.amazon.com/code-library/latest/ug/transcribe_example_cross_TranscriptionApp_section.html",
        },
        "sdk_pages": {
            "JavaScript": {
                3: {
                    "cross_service": {
                        "cross": "https://docs.aws.amazon.com/code-library/latest/ug/cross_TranscriptionStreamingApp_javascript_3_topic.html"
                    }
                }
            }
        },
    }

    # A multi service scenario
    resilient_service.doc_file_names == {
        "service_pages": {
            "auto-scaling": "https://docs.aws.amazon.com/code-library/latest/ug/auto-scaling_example_cross_ResilientService_section.html",
            "ec2": "https://docs.aws.amazon.com/code-library/latest/ug/ec2_example_cross_ResilientService_section.html",
        },
        "sdk_pages": {
            "JavaScript": {
                3: {
                    "actions_scenarios": {
                        "auto-scaling": "https://docs.aws.amazon.com/code-library/latest/ug/javascript_3_auto-scaling_code_examples.html",
                        "ec2": "https://docs.aws.amazon.com/code-library/latest/ug/javascript_3_ec2_code_examples.html"
                    }
                }
            },
        },
    }
    ```
    """

    service_pages: Optional[ServicePages] = None
    sdk_pages: Optional[SDKPages] = None


def get_doc_filenames(example_id: str, example: Example) -> Optional[DocFilenames]:
    base_url = "https://docs.aws.amazon.com/code-library/latest/ug"
    service_pages = {
        service_id: f"{base_url}/{service_id}_example_{example_id}_section.html"
        for service_id in example.services
    }

    if example.file is not None:
        is_cross = example.file.match("cross_*")
    else:
        is_cross = False

    sdk_pages: SDKPages = {}

    for language in example.languages.values():
        sdk_pages[language.property] = {}
        for version in language.versions:
            if is_cross:
                sdk_pages[language.property][version.sdk_version] = SDKPageVersion(
                    cross_service=CrossServicePage(
                        cross=f"{base_url}/{example_id}_{language.property}_{version.sdk_version}_topic.html"
                    )
                )
            else:
                anchor = "actions" if example.category == "Actions" else "scenarios"
                sdk_pages[language.property][version.sdk_version] = SDKPageVersion(
                    actions_scenarios={
                        service_id: f"{base_url}/{language.property}_{version.sdk_version}_{service_id}_code_examples.html#{anchor}"
                        for service_id in example.services
                    }
                )

    return DocFilenames(service_pages, sdk_pages)


def get_with_valid_entities(
    name: str, d: Dict[str, str], errors: MetadataErrors, opt: bool = False
) -> str:
    field = d.get(name)
    if field is None:
        if not opt:
            errors.append(metadata_errors.MissingField(field=name))
        return ""

    checker = StringExtension()
    if not checker.is_valid(field):
        errors.append(
            metadata_errors.AwsNotEntity(
                field=name, value=field, check_err=checker.get_name()
            )
        )
        return ""
    return field


def check_id_format(
    id: str,
    parsed_services: Dict[str, set[str]],
    check_action: bool,
    errors: MetadataErrors,
):
    [service, *rest] = id.split("_")
    if len(rest) == 0:
        errors.append(metadata_errors.NameFormat(id=id))
    elif service not in parsed_services and service not in ["cross", "serverless"]:
        errors.append(
            metadata_errors.ServiceNameFormat(
                id=id, svc=service, svcs=[*parsed_services.keys()]
            )
        )
    elif check_action and (
        len(rest) > 1 or rest[0] not in parsed_services.get(service, {})
    ):
        errors.append(metadata_errors.ActionNameFormat(id=id))


def parse(
    file: Path,
    yaml: Dict[str, Any],
    sdks: Dict[str, Sdk],
    services: Dict[str, Service],
    blocks: Set[str],
    validation: Optional[ValidationConfig],
    root: Optional[Path] = None,
) -> tuple[List[Example], MetadataErrors]:
    examples: List[Example] = []
    errors = MetadataErrors()
    validation = validation or ValidationConfig()
    for id in yaml:
        example, example_errors = Example.from_yaml(
            yaml[id], sdks, services, blocks, validation, root or file.parent
        )
        check_id_format(
            id,
            example.services,
            validation.strict_titles and example.category == "Api",
            example_errors,
        )
        for error in example_errors:
            error.file = file
            error.id = id
        errors.extend(example_errors)
        example.file = file
        example.id = id
        example.doc_filenames = get_doc_filenames(id, example)
        examples.append(example)

    return examples, errors


def validate_no_duplicate_api_examples(
    examples: Iterable[Example], errors: MetadataErrors
):
    """Call this on a full set of examples to verify that there are no duplicate API examples."""
    svc_action_map: Dict[str, List[str]] = defaultdict(list)
    title_abbr_map: Dict[str, Dict[str, List[str]]] = defaultdict(
        lambda: defaultdict(list)
    )
    for example in examples:
        if example.category == "Api":
            for service, actions in example.services.items():
                for action in actions:
                    svc_action_map[f"{service}:{action}"].append(example.id)
        if example.title_abbrev:
            for service in example.services.keys():
                title_abbr_map[example.title_abbrev][
                    f"{service}:{example.category}"
                ].append(example.id)
    for svc_action, ex_items in svc_action_map.items():
        if len(ex_items) > 1:
            errors.append(
                metadata_errors.DuplicateAPIExample(
                    id=", ".join({ex_item for ex_item in ex_items}),
                    svc_action=svc_action,
                    duplicates=ex_items,
                )
            )
    for title_abbrev, languages in title_abbr_map.items():
        for lang, ids in languages.items():
            if len(ids) > 1:
                errors.append(
                    metadata_errors.DuplicateTitleAbbrev(
                        id=", ".join(ids),
                        title_abbrev=title_abbrev,
                        language=lang,
                    )
                )


def main():
    import yaml
    from pathlib import Path

    path = (
        Path(__file__).parent.parent.parent
        / ".doc_gen"
        / "metadata"
        / "s3_metadata.yaml"
    )
    with open(path) as file:
        meta = yaml.safe_load(file)
    (examples, errors) = parse(path, meta, {}, {}, set(), ValidationConfig())
    if len(errors) > 0:
        print(f"{errors}")
    else:
        print(f"{examples!r}")


if __name__ == "__main__":
    main()
