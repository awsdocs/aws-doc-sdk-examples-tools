# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field

from aws_doc_sdk_examples_tools import metadata_errors
from .metadata_errors import (
    MetadataErrors,
    MetadataParseError,
    check_mapping,
)


@dataclass
class Category:
    key: str
    title: str
    title_abbrev: str
    display: str
    description: str

    @classmethod
    def from_yaml(cls, key: str, yaml: Dict[str, Any]) -> tuple[Category, MetadataErrors]:
        errors = MetadataErrors()
        display = yaml.get("display", "")
        description = yaml.get("description", "")
        title = yaml.get("title", "")
        title_abbrev = yaml.get("title_abbrev", "")

        return cls(key=key, display=display, description=description, title=title, title_abbrev=title_abbrev), errors


def parse(file: Path, yaml: Dict[str, Any]) -> tuple[Dict[str, Category], MetadataErrors]:
    categories: Dict[str, Category] = {}
    errors = MetadataErrors()

    for key in yaml:
        category, errs = Category.from_yaml(key, yaml[key])
        categories[key] = category
        for error in errs:
            error.file = file
            error.id = key
        errors.extend(errs)

    return categories, errors


if __name__ == "__main__":
    from pprint import pp
    import yaml

    path = Path(__file__).parent / "config" / "categories.yaml"
    with open(path) as file:
        meta = yaml.safe_load(file)
    categories, errors = parse(path, meta)
    pp(categories)
