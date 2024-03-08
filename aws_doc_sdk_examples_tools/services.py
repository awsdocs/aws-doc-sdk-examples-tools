# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from typing import Any, Dict, Optional, Set, Union
from dataclasses import dataclass, field
from aws_doc_sdk_examples_tools import metadata_errors
from aws_doc_sdk_examples_tools.metadata_errors import MetadataErrors, check_mapping


@dataclass
class ServiceGuide:
    subtitle: str
    url: str


@dataclass
class Service:
    long: str
    expanded_long: str
    short: str
    expanded_short: str
    sort: str
    version: Union[int, str]
    api_ref: Optional[str] = field(default=None)
    blurb: Optional[str] = field(default=None)
    bundle: Optional[str] = field(default=None)
    caveat: Optional[str] = field(default=None)
    guide: Optional[ServiceGuide] = field(default=None)
    tags: Dict[str, Set[str]] = field(default_factory=dict)

    @classmethod
    def from_yaml(
        cls, name: str, yaml: Dict[str, Any]
    ) -> tuple[Service, MetadataErrors]:
        errors = MetadataErrors()

        long = check_mapping(yaml.get("long"), "long")
        expanded_long = yaml.get("expanded", {}).get("long")
        short = check_mapping(yaml.get("short"), "short")
        expanded_short = yaml.get("expanded", {}).get("short")
        sort = yaml.get("sort")
        version = yaml.get("version")

        if isinstance(long, metadata_errors.MetadataParseError):
            errors.append(long)
            long = ""
        if isinstance(short, metadata_errors.MetadataParseError):
            errors.append(short)
            short = ""
        if expanded_long is None:
            errors.append(metadata_errors.MissingField(field="expanded_long"))
            expanded_long = ""
        if expanded_short is None:
            errors.append(metadata_errors.MissingField(field="expanded_short"))
            expanded_short = ""
        if sort is None:
            errors.append(metadata_errors.MissingField(field="sort"))
            sort = ""
        if version is None:
            errors.append(metadata_errors.MissingField(field="version"))
            version = "0"

        api_ref = yaml.get("api_ref")
        blurb = yaml.get("blurb")
        caveat = yaml.get("caveat")
        bundle = yaml.get("bundle")

        guide = yaml.get("guide")
        if guide is not None:
            subtitle = guide.get("subtitle")
            url = guide.get("url")
            if subtitle is None:
                errors.append(metadata_errors.MissingField(field="guide.subtitle"))
            if url is None:
                errors.append(metadata_errors.MissingField(field="guide.url"))
            guide = ServiceGuide(subtitle=subtitle, url=url)

        tags = yaml.get("tags", {})
        for tag in tags:
            tags[tag] = set(tags[tag].keys())

        for error in errors:
            error.id = name

        return (
            cls(
                long=long,
                expanded_long=expanded_long,
                short=short,
                expanded_short=expanded_short,
                sort=sort,
                api_ref=api_ref,
                blurb=blurb,
                bundle=bundle,
                caveat=caveat,
                guide=guide,
                tags=tags,
                version=version,
            ),
            errors,
        )


def parse(
    filename: str, yaml: Dict[str, Any]
) -> tuple[Dict[str, Service], MetadataErrors]:
    errors = metadata_errors.MetadataErrors()
    services: Dict[str, Service] = {}
    for name in yaml:
        meta = yaml[name]
        if meta is None:
            errors.append(metadata_errors.MissingServiceBody(file=filename, id=name))
        else:
            service, service_errors = Service.from_yaml(name, meta)
            for error in service_errors:
                error.file = filename
            errors.extend(service_errors)
            services[name] = service

    return services, errors


if __name__ == "__main__":
    import yaml
    from pathlib import Path

    path = (
        Path(__file__).parent.parent.parent / ".doc_gen" / "metadata" / "services.yaml"
    )
    with open(path) as file:
        meta = yaml.safe_load(file)
    examples = parse(path.name, meta)
    print(f"{examples}")
