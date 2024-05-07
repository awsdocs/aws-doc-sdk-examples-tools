# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Optional, Iterator, Iterable, List, TypeVar


@dataclass
class MetadataError:
    file: Optional[str] = None
    id: Optional[str] = None

    def prefix(self):
        prefix = f"In {self.file} at {self.id},"
        return prefix

    def message(self) -> str:
        return ""

    def __str__(self):
        return f"{self.prefix()} {self.message()}"


@dataclass
class MetadataParseError(MetadataError):
    id: Optional[str] = None
    language: Optional[str] = None
    sdk_version: Optional[int] = None

    def prefix(self):
        prefix = super().prefix() + f" example {self.id}"
        if self.language:
            prefix += f" {self.language}"
        if self.sdk_version:
            prefix += f":{self.sdk_version}"
        return prefix

    def __str__(self):
        return f"{self.prefix()} {self.message()}"


K = TypeVar("K")


class InvalidItemException(Exception):
    def __init__(self, item: MetadataParseError):
        super().__init__(self, f"Cannot append {item!r} to ExampleErrors")


class DuplicateItemException(Exception):
    def __init__(self, item: MetadataError):
        super().__init__(self, f"Already have item {item!r} in ExampleErrors")


class MetadataErrors:
    """MyPy isn't catching List[Foo].append(List[Foo])"""

    def __init__(self, no_duplicates: bool = False):
        self.no_duplicates = no_duplicates
        self._errors: List[MetadataError] = []

    def append(self, item: MetadataError):
        if not isinstance(item, MetadataError):
            raise InvalidItemException(item)
        """
        It is dangerous to go alone: 🗡️
        If you're seeing duplicated Errors, and aren't sure why, uncommenting these lines may help you debug it.
        """
        # if item in self._errors:
        #     raise DuplicateItemException(item)
        self._errors.append(item)

    def extend(self, errors: Iterable[MetadataError]):
        self._errors.extend(errors)

    def maybe_extend(self, maybe_errors: K | MetadataErrors) -> K | None:
        if isinstance(maybe_errors, MetadataErrors):
            self.extend(maybe_errors._errors)
            return None
        return maybe_errors

    def __getitem__(self, key: int) -> MetadataError:
        return self._errors[key]

    def __setitem__(self, key: int, value: MetadataError):
        self._errors[key] = value

    def __len__(self) -> int:
        return len(self._errors)

    def __iter__(self) -> Iterator[MetadataError]:
        return self._errors.__iter__()

    def __repr__(self) -> str:
        return repr(self._errors)

    def __str__(self) -> str:
        errs = "\n".join([f"\t{err}" for err in self._errors])
        return f"ExampleErrors with {len(self)} errors:\n{errs}"

    def __eq__(self, __value: object) -> bool:
        return isinstance(__value, MetadataErrors) and self._errors == __value._errors


@dataclass
class MissingServiceBody(MetadataParseError):
    def message(self):
        return "service definition missing body"


@dataclass
class NamePrefixMismatch(MetadataParseError):
    def message(self):
        return "name prefix does not match any known service."


@dataclass
class NameFormat(MetadataParseError):
    def message(self):
        return "name does not match the required format of 'svc_Operation', 'svc_Operation_Specialization', or 'cross_Title'"


@dataclass
class ServiceNameFormat(NameFormat):
    svc: str = ""
    svcs: list[str] = field(default_factory=list)

    def message(self):
        return (
            NameFormat.message(self)
            + f" (service {self.svc}, services {', '.join(self.svcs)})"
        )


@dataclass
class ActionNameFormat(MetadataParseError):
    def message(self):
        return "name of API example does not match the required format of 'svc_Action'"


@dataclass
class MissingCrossContent(MetadataParseError):
    block: str = ""

    def message(self):
        return f"missing cross content block {self.block}"


@dataclass
class FieldError(MetadataParseError):
    field: str = ""
    value: str = ""


@dataclass
class MissingField(FieldError):
    def message(self):
        return f"missing field {self.field}"


@dataclass
class AwsNotEntity(FieldError):
    check_err: str = ""

    def message(self):
        return f"field {self.field} is '{self.value}', which has a validation issue: {self.check_err}."


@dataclass
class MappingMustBeEntity(FieldError):
    def message(self):
        return f"Mapping field {self.field} with value {self.value} must be an entity."


@dataclass
class LanguagesEmptyError(MetadataParseError):
    def message(self):
        return "does not contain any languages."


@dataclass
class LanguageError(MetadataParseError):
    def message(self) -> str:
        return "LanguageError?"


@dataclass
class UnknownLanguage(LanguageError):
    def message(self):
        return (
            f"contains {self.language} as a language, which is not listed in sdks.yaml."
        )


@dataclass
class MissingBlockContent(LanguageError):
    block_content: str = ""

    def message(self):
        return f"block_content {self.block_content} was not found in the cross-contents folder."


@dataclass
class BlockContentAndExcerptConflict(LanguageError):
    def message(self):
        return "contains both block_content and excerpt data. You cannot use both."


@dataclass
class MissingBlockContentAndExcerpt(LanguageError):
    def message(self):
        return "must contain either block_content or excerpt data."


@dataclass
class SdkVersionError(LanguageError):
    def message(self) -> str:
        return "SdkVersionError"


@dataclass
class InvalidSdkVersion(SdkVersionError):
    def message(self):
        return "lists version which is not listed in sdks.yaml."


@dataclass
class InvalidGithubLink(SdkVersionError):
    link: str = ""

    def message(self):
        return f"has link {self.link}, which looks like a file. Links to Github should be to the folder that contains the README that describes the example."


@dataclass
class InvalidSdkGuideStart(SdkVersionError):
    guide: str = ""

    def message(self):
        return f"contains an sdkguide link of '{self.guide}'. Use a relative link instead and let the tool insert a 'type=documentation' attribute in the link on your behalf."


@dataclass
class APIExampleCannotAddService(SdkVersionError):
    def message(self):
        return (
            "is an API example but lists additional services in the add_service field."
        )


@dataclass
class APIMustHaveOneServiceOneAction(MetadataParseError):
    svc_actions: str = ""

    def message(self):
        return (
            f"is an API example but lists svc:actions as '{self.svc_actions}'. "
            f"API examples must contain exactly one service and one action."
        )


@dataclass
class APICannotHaveTitleFields(MetadataParseError):
    def message(self):
        return (
            f"is an API example and defines title, title_abbrev, or synopsis. "
            f"API examples cannot define these fields because they are generated."
        )


@dataclass
class NonAPIMustHaveTitleFields(MetadataParseError):
    def message(self):
        return (
            f"is not an API example and does not define title, title_abbrev, or synopsis. "
            f"Non-API examples must define these fields."
        )


@dataclass
class MissingSnippetTag(SdkVersionError):
    tag: str = ""

    def message(self):
        return f" excerpt {self.tag} not found in the snippets folder."


@dataclass
class UnknownService(MetadataParseError):
    service: str = ""

    def message(self):
        return f"has unknown service {self.service}"


@dataclass
class DuplicateService(MetadataParseError):
    services: str = ""

    def message(self):
        return f"service {self.services} listed more than once"


@dataclass
class DuplicateExample(MetadataParseError):
    other_file: str = ""

    def message(self):
        return f"also found in {self.other_file}"


@dataclass
class DuplicateAPIExample(MetadataError):
    svc_action: str = ""

    def message(self):
        return f"multiple API examples found for service:action {self.svc_action}"


@dataclass
class URLMissingTitle(SdkVersionError):
    url: str = ""

    def message(self):
        return f"URL {self.url} is missing a title"


def check_mapping(mapping: str | None, field: str) -> str | MetadataParseError:
    if not mapping:
        return MissingField(field=field)
    if not re.match("&[-_a-zA-Z0-9]+;", mapping):
        return MappingMustBeEntity(field=field, value=mapping)

    return mapping
