# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field

from aws_doc_sdk_examples_tools import metadata_errors
from .metadata_errors import (
    MetadataErrors,
)


@dataclass
class TitleInfo:
    title: Optional[str] = field(default=None)
    title_abbrev: Optional[str] = field(default=None)
    synopsis: Optional[str] = field(default=None)
    title_suffixes: str | Dict[str, str] = field(default_factory=dict)

    @classmethod
    def from_yaml(cls, yaml: Dict[str, str] | None) -> Optional[TitleInfo]:
        if yaml is None:
            return None

        title = yaml.get("title")
        title_suffixes: str | Dict[str, str] = yaml.get("title_suffixes", {})
        title_abbrev = yaml.get("title_abbrev")
        synopsis = yaml.get("synopsis")

        return cls(title=title, title_suffixes=title_suffixes, title_abbrev=title_abbrev, synopsis=synopsis)


@dataclass
class CategoryWithNoDisplayError(metadata_errors.MetadataError):
    def message(self):
        return "Category has no display value"


@dataclass
class Category:
    key: str
    display: str
    defaults: Optional[TitleInfo] = field(default=None)
    overrides: Optional[TitleInfo] = field(default=None)
    description: Optional[str] = field(default=None)

    def validate(self, errors: MetadataErrors):
        if not self.display:
            errors.append(CategoryWithNoDisplayError(id=self.key))

    @classmethod
    def from_yaml(cls, key: str, yaml: Dict[str, Any]) -> tuple[Category, MetadataErrors]:
        errors = MetadataErrors()
        display = str(yaml.get("display"))
        defaults = TitleInfo.from_yaml(yaml.get("defaults"))
        overrides = TitleInfo.from_yaml(yaml.get("overrides"))
        description = yaml.get("description")

        return cls(key=key, display=display, defaults=defaults, overrides=overrides, description=description), errors


def parse(file: Path, yaml: Dict[str, Any]) -> tuple[List[str], Dict[str, Category], MetadataErrors]:
    categories: Dict[str, Category] = {}
    errors = MetadataErrors()

    standard_cats = yaml.get("standard_categories", [])
    # Work around inconsistency where some tools use 'Actions' and DocGen uses 'Api' to refer to single-action examples.
    for i in range(len(standard_cats)):
        if standard_cats[i] == "Actions":
            standard_cats[i] = "Api"
    for key, yaml_cat in yaml.get("categories", {}).items():
        if yaml_cat is None:
            errors.append(metadata_errors.MissingCategoryBody(id=key, file=file))
        else:
            category, cat_errs = Category.from_yaml(key, yaml_cat)
            categories[key] = category
            for error in cat_errs:
                error.file = file
                error.id = key
            errors.extend(cat_errs)

    return standard_cats, categories, errors


if __name__ == "__main__":
    from pprint import pp
    import yaml

    path = Path(__file__).parent / "config" / "categories.yaml"
    with open(path) as file:
        meta = yaml.safe_load(file)
    standard_cats, cats, errs = parse(path, meta)
    pp(standard_cats)
    pp(cats)
