# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

import yaml

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Iterable, Optional, Set

# from os import glob

from .metadata import Example, parse as parse_examples
from .metadata_errors import MetadataErrors, MetadataError
from .metadata_validator import validate_metadata
from .project_validator import (
    check_files,
    verify_sample_files,
)
from .sdks import Sdk, parse as parse_sdks
from .services import Service, parse as parse_services
from .snippets import (
    Snippet,
    collect_snippets,
    validate_snippets,
)


@dataclass
class DocGenMergeWarning(MetadataError):
    pass


@dataclass
class DocGen:
    root: Path
    errors: MetadataErrors
    sdks: Dict[str, Sdk] = field(default_factory=dict)
    services: Dict[str, Service] = field(default_factory=dict)
    snippets: Dict[str, Snippet] = field(default_factory=dict)
    snippet_files: Set[str] = field(default_factory=set)
    examples: Dict[str, Example] = field(default_factory=dict)
    cross_blocks: Set[str] = field(default_factory=set)

    def collect_snippets(
        self, snippets_root: Optional[Path] = None, prefix: Optional[str] = None
    ):
        if prefix is not None:
            prefix = f"{prefix}_"
        if prefix is None:
            prefix = ""
        if snippets_root is None:
            snippets_root = self.root
        snippets, errs = collect_snippets(snippets_root, prefix)
        self.snippets = snippets
        self.errors.extend(errs)

    def languages(self) -> Set[str]:
        languages: Set[str] = set()
        for sdk_name, sdk in self.sdks.items():
            for version in sdk.versions:
                languages.add(f"{sdk_name}:{version.version}")
        return languages

    def merge(self, other: "DocGen") -> MetadataErrors:
        """Merge fiends from other into self, prioritizing self fields"""
        warnings = MetadataErrors()
        for name, sdk in other.sdks.items():
            if name not in self.sdks:
                self.sdks[name] = sdk
            else:
                warnings.append(
                    DocGenMergeWarning(
                        file=str(other.root), id=f"conflict in sdk {name}"
                    )
                )
        for name, service in other.services.items():
            if name not in self.services:
                self.services[name] = service
                warnings.append(
                    DocGenMergeWarning(
                        file=str(other.root), id=f"conflict in service {name}"
                    )
                )
        for name, snippet in other.snippets.items():
            if name not in self.snippets:
                self.snippets[name] = snippet
                warnings.append(
                    DocGenMergeWarning(
                        file=str(other.root), id=f"conflict in snippet {name}"
                    )
                )

        self.snippet_files.update(other.snippet_files)
        self.cross_blocks.update(other.cross_blocks)
        self.extend_examples(other.examples.values())

        return warnings

    def extend_examples(self, examples: Iterable[Example]):
        for example in examples:
            id = example.id
            if id in self.examples:
                self.examples[id].merge(example, self.errors)
            else:
                self.examples[id] = example

    @classmethod
    def empty(cls) -> "DocGen":
        return DocGen(root=Path("/"), errors=MetadataErrors())

    def clone(self) -> "DocGen":
        return DocGen(
            root=self.root,
            errors=MetadataErrors(),
            sdks={**self.sdks},
            services={**self.services},
            snippets={},
            snippet_files=set(),
            cross_blocks=set(),
            examples={},
        )

    def for_root(self, root: Path, config: Optional[Path] = None) -> "DocGen":
        self.root = root
        metadata = root / ".doc_gen/metadata"

        if config is None:
            config = Path(__file__).parent / "config"

        with open(config / "sdks.yaml", encoding="utf-8") as file:
            meta = yaml.safe_load(file)
            sdks, errs = parse_sdks("sdks.yaml", meta)
            self.errors.extend(errs)

        with open(config / "services.yaml", encoding="utf-8") as file:
            meta = yaml.safe_load(file)
            services, service_errors = parse_services("services.yaml", meta)
            self.errors.extend(service_errors)

        cross = set(
            [path.name for path in (metadata.parent / "cross-content").glob("*.xml")]
        )

        self.root = root
        self.sdks = sdks
        self.services = services
        self.cross_blocks = cross

        for path in metadata.glob("*_metadata.yaml"):
            with open(path) as file:
                examples, errs = parse_examples(
                    path.name,
                    yaml.safe_load(file),
                    self.sdks,
                    self.services,
                    self.cross_blocks,
                )
                self.extend_examples(examples)
                self.errors.extend(errs)
                for example in examples:
                    for lang in example.languages:
                        language = example.languages[lang]
                        for version in language.versions:
                            for excerpt in version.excerpts:
                                self.snippet_files.update(excerpt.snippet_files)

        return self

    @classmethod
    def from_root(cls, root: Path, config: Optional[Path] = None) -> "DocGen":
        return DocGen.empty().for_root(root, config)

    def validate(self, check_spdx: bool):
        check_files(self.root, self.errors, check_spdx)
        verify_sample_files(self.root, self.errors)
        validate_metadata(self.root, self.errors)
        validate_snippets(
            [*self.examples.values()],
            self.snippets,
            self.snippet_files,
            self.errors,
            self.root,
        )
