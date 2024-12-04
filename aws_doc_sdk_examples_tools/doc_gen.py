# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

import yaml
import json

from collections import defaultdict
from dataclasses import dataclass, field, is_dataclass, asdict
from functools import reduce
from pathlib import Path
from typing import Dict, Iterable, Optional, Set, Tuple, List, Any

# from os import glob

from .metadata import (
    Example,
    DocFilenames,
    SDKPages,
    SDKPageVersion,
    CrossServicePage,
    validate_no_duplicate_api_examples,
)
from .entities import expand_all_entities, EntityErrors
from .metadata_errors import (
    MetadataErrors,
    MetadataError,
    NameFormat,
    ActionNameFormat,
    ServiceNameFormat,
)
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
from .yaml_mapper import example_from_yaml


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
        validate_metadata(self.root, self.validation.strict_titles, self.errors)
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


def parse_examples(
    file: Path,
    yaml: Dict[str, Any],
    sdks: Dict[str, Sdk],
    services: Dict[str, Service],
    blocks: Set[str],
    validation: Optional[ValidationConfig],
    root: Optional[Path] = None,
) -> Tuple[List[Example], MetadataErrors]:
    examples: List[Example] = []
    errors = MetadataErrors()
    validation = validation or ValidationConfig()
    for id in yaml:
        example, example_errors = example_from_yaml(
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


def check_id_format(
    id: str,
    parsed_services: Dict[str, Set[str]],
    check_action: bool,
    errors: MetadataErrors,
):
    [service, *rest] = id.split("_")
    if len(rest) == 0:
        errors.append(NameFormat(id=id))
    elif service not in parsed_services and service not in ["cross", "serverless"]:
        errors.append(
            ServiceNameFormat(id=id, svc=service, svcs=[*parsed_services.keys()])
        )
    elif check_action and (
        len(rest) > 1 or rest[0] not in parsed_services.get(service, {})
    ):
        errors.append(ActionNameFormat(id=id))


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
