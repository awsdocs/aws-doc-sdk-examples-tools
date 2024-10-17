# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

import yaml
import json

from collections import defaultdict
from dataclasses import dataclass, field, is_dataclass, asdict
from functools import reduce
from pathlib import Path
from typing import Dict, Iterable, Optional, Set, Tuple

# from os import glob

from .metadata import (
    Example,
    parse as parse_examples,
    validate_no_duplicate_api_examples,
)
from .entities import expand_all_entities, EntityErrors
from .metadata_errors import MetadataErrors, MetadataError
from .metadata_validator import validate_metadata
from .project_validator import ValidationConfig
from .sdks import Sdk, parse as parse_sdks
from .services import Service, parse as parse_services
from .snippets import (
    Snippet,
    collect_snippets,
    collect_snippet_files,
    validate_snippets,
)


@dataclass
class DocGenMergeWarning(MetadataError):
    pass


@dataclass
class DocGen:
    root: Path
    errors: MetadataErrors
    entities: Dict[str, str] = field(default_factory=dict)
    prefix: Optional[str] = None
    validation: ValidationConfig = field(default_factory=ValidationConfig)
    sdks: Dict[str, Sdk] = field(default_factory=dict)
    services: Dict[str, Service] = field(default_factory=dict)
    snippets: Dict[str, Snippet] = field(default_factory=dict)
    snippet_files: Set[str] = field(default_factory=set)
    examples: Dict[str, Example] = field(default_factory=dict)
    cross_blocks: Set[str] = field(default_factory=set)
    _loaded: Set[Path] = field(default_factory=set, init=False)

    def collect_snippets(
        self, snippets_root: Optional[Path] = None, prefix: Optional[str] = None
    ):
        prefix = prefix or ""
        snippets_root = snippets_root or self.root
        snippets, errs = collect_snippets(snippets_root)
        collect_snippet_files(
            self.examples.values(),
            prefix=prefix,
            snippets=snippets,
            errors=errs,
            root=self.root,
        )
        self.snippets = snippets
        self.errors.extend(errs)

    def languages(self) -> Set[str]:
        languages: Set[str] = set()
        for sdk_name, sdk in self.sdks.items():
            for version in sdk.versions:
                languages.add(f"{sdk_name}:{version.version}")
        return languages

    def expand_entities(self, text: str) -> Tuple[str, EntityErrors]:
        return expand_all_entities(text, self.entities)

    def merge(self, other: "DocGen") -> MetadataErrors:
        """Merge fields from other into self, prioritizing self fields."""
        warnings = MetadataErrors()
        for name, sdk in other.sdks.items():
            if name not in self.sdks:
                self.sdks[name] = sdk
            else:
                warnings.append(
                    DocGenMergeWarning(file=other.root, id=f"conflict in sdk {name}")
                )
        for name, service in other.services.items():
            if name not in self.services:
                self.services[name] = service
                warnings.append(
                    DocGenMergeWarning(
                        file=other.root, id=f"conflict in service {name}"
                    )
                )
        for name, snippet in other.snippets.items():
            if name not in self.snippets:
                self.snippets[name] = snippet
                warnings.append(
                    DocGenMergeWarning(
                        file=other.root, id=f"conflict in snippet {name}"
                    )
                )

        for entity, expanded in other.entities.items():
            if entity not in self.entities:
                self.entities[entity] = expanded
            else:
                warnings.append(
                    DocGenMergeWarning(
                        file=other.root, id=f"conflict in entity {entity}"
                    )
                )

        self.validation.allow_list.update(other.validation.allow_list)
        self.validation.sample_files.update(other.validation.sample_files)
        self.snippet_files.update(other.snippet_files)
        self.cross_blocks.update(other.cross_blocks)
        self.extend_examples(other.examples.values(), warnings)

        return warnings

    def extend_examples(self, examples: Iterable[Example], errors: MetadataErrors):
        for example in examples:
            id = example.id
            if id in self.examples:
                self.examples[id].merge(example, errors)
            else:
                self.examples[id] = example

    @classmethod
    def empty(cls, validation: ValidationConfig = ValidationConfig()) -> "DocGen":
        return DocGen(root=Path("/"), errors=MetadataErrors(), validation=validation)

    @classmethod
    def default(cls) -> "DocGen":
        return DocGen.empty().for_root(Path(__file__).parent, incremental=True)

    def clone(self) -> "DocGen":
        return DocGen(
            root=self.root,
            errors=MetadataErrors(),
            validation=self.validation.clone(),
            sdks={**self.sdks},
            services={**self.services},
            snippets={},
            snippet_files=set(),
            cross_blocks=set(),
            examples={},
        )

    def for_root(
        self, root: Path, config: Optional[Path] = None, incremental=False
    ) -> "DocGen":
        self.root = root

        config = config or Path(__file__).parent / "config"

        try:
            with open(root / ".doc_gen" / "validation.yaml", encoding="utf-8") as file:
                validation = yaml.safe_load(file)
                validation = validation or {}
                self.validation.allow_list.update(validation.get("allow_list", []))
                self.validation.sample_files.update(validation.get("sample_files", []))
        except Exception:
            pass

        try:
            sdk_path = config / "sdks.yaml"
            with sdk_path.open(encoding="utf-8") as file:
                meta = yaml.safe_load(file)
                sdks, errs = parse_sdks(sdk_path, meta)
                self.sdks = sdks
                self.errors.extend(errs)
        except Exception:
            pass

        try:
            services_path = config / "services.yaml"
            with services_path.open(encoding="utf-8") as file:
                meta = yaml.safe_load(file)
                services, service_errors = parse_services(services_path, meta)
                self.services = services
                for service in self.services.values():
                    if service.expanded:
                        self.entities[service.long] = service.expanded.long
                        self.entities[service.short] = service.expanded.short
                self.errors.extend(service_errors)
        except Exception:
            pass

        try:
            entities_config_path = config / "entities.yaml"
            with entities_config_path.open(encoding="utf-8") as file:
                entities_config = yaml.safe_load(file)
            for entity, expanded in entities_config["expanded_override"].items():
                self.entities[entity] = expanded
        except Exception:
            pass

        metadata = root / ".doc_gen/metadata"
        try:
            self.cross_blocks = set(
                [
                    path.name
                    for path in (metadata.parent / "cross-content").glob("*.xml")
                ]
            )
        except Exception:
            pass

        if not incremental:
            for path in metadata.glob("*_metadata.yaml"):
                self.process_metadata(path)

        return self

    def process_metadata(self, path: Path) -> "DocGen":
        if path in self._loaded:
            return self
        with open(path) as file:
            examples, errs = parse_examples(
                path,
                yaml.safe_load(file),
                self.sdks,
                self.services,
                self.cross_blocks,
                self.validation,
                self.root,
            )
            self.extend_examples(examples, self.errors)
            self.errors.extend(errs)
            for example in examples:
                for lang in example.languages:
                    language = example.languages[lang]
                    for version in language.versions:
                        for excerpt in version.excerpts:
                            self.snippet_files.update(excerpt.snippet_files)
        self._loaded.add(path)
        return self

    @classmethod
    def from_root(
        cls,
        root: Path,
        config: Optional[Path] = None,
        validation: ValidationConfig = ValidationConfig(),
        incremental: bool = False,
    ) -> "DocGen":
        return DocGen.empty(validation=validation).for_root(
            root, config, incremental=incremental
        )

    def validate(self):
        for sdk in self.sdks.values():
            sdk.validate(self.errors)
        for service in self.services.values():
            service.validate(self.errors)
        for example in self.examples.values():
            example.validate(self.errors, self.root)
        validate_metadata(self.root, self.errors)
        validate_no_duplicate_api_examples(self.examples.values(), self.errors)
        validate_snippets(
            [*self.examples.values()],
            self.snippets,
            self.validation,
            self.errors,
            self.root,
        )

    def stats(self):
        values = self.examples.values()
        initial = defaultdict(int)

        def count_genai(d: Dict[str, int], e: Example):
            for lang in e.languages.values():
                for version in lang.versions:
                    for excerpt in version.excerpts:
                        d[excerpt.genai] += 1
            return d

        genai = reduce(count_genai, values, initial)

        return {
            "sdks": len(self.sdks),
            "services": len(self.services),
            "examples": len(self.examples),
            "versions": sum(
                sum(len(lang.versions) for lang in e.languages.values())
                for e in self.examples.values()
            ),
            "snippets": len(self.snippets) + len(self.snippet_files),
            "genai": dict(genai),
        }


# Encode a DocGen instance as JSON. Originally
# it was planned to have a DocGenDecoder as well,
# but that required writing environment data like
# Path to the JSON, which was not very secure
# and arguably not useful either.
class DocGenEncoder(json.JSONEncoder):
    def default(self, obj):
        if is_dataclass(obj):
            return asdict(obj)

        if isinstance(obj, Path):
            # Strip out paths to prevent leaking environment data.
            return obj.name

        if isinstance(obj, MetadataErrors):
            return {"__metadata_errors__": [asdict(error) for error in obj]}

        if isinstance(obj, EntityErrors):
            return {
                "__entity_errors__": [{error.entity: error.message()} for error in obj]
            }

        if isinstance(obj, set):
            return {"__set__": list(obj)}

        return super().default(obj)
