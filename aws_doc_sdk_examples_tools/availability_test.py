#!/usr/bin/env python3
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

"""Tests for the feature-level example fields: description, available_since,
available_since_version and introduced_operations.

The metadata fixtures use the exact form the code example generator's metadata
finalizer writes: one key per line, value as single-line JSON, inserted at the
top of the scenario entry.
"""

from pathlib import Path
from typing import Dict, List, Optional

import pytest
import yaml

from . import metadata_errors
from .doc_gen import DocGen
from .metadata import AvailabilityVersion, Example, Language
from .metadata_errors import MetadataErrors
from .metadata_validator import validate_metadata
from .yaml_writer import prepare_write

DESCRIPTION = (
    # Starts with an entity, as every live finalizer description does.
    '"&S3long; (&S3;) object annotations let you attach named metadata payloads '
    'to objects, using <code>PutObjectAnnotation</code>."'
)
VERSIONS = (
    '{"Python": {"version": "1.43.31", "major": "3", "basis": "exact"}, '
    '"PowerShell": {"version": "5.0.0", "major": "5", "basis": "at_least"}}'
)
OPERATIONS = '["PutObjectAnnotation", "GetObjectAnnotation"]'

BODY = """\
  title: Work with &S3; object annotations using an &AWS; SDK
  title_abbrev: Work with object annotations
  synopsis: work with object annotations.
  category: Scenarios
  languages:
    Python:
      versions:
        - sdk_version: 3
          github: python/example_code/s3
          excerpts:
            - description: Run the scenario.
              snippet_tags:
                - python.example_code.s3.ObjectAnnotations
  services:
    s3: {PutObjectAnnotation, GetObjectAnnotation}
"""


def entry(**fields: Optional[str]) -> str:
    """A scenario entry with ``fields`` written the way the finalizer writes them."""
    lines = [f"  {key}: {value}" for key, value in fields.items() if value is not None]
    return "s3_Scenario_ObjectAnnotations:\n" + "".join(l + "\n" for l in lines) + BODY


FULL = entry(
    description=DESCRIPTION,
    available_since='"2026-06-16"',
    available_since_version=VERSIONS,
    introduced_operations=OPERATIONS,
)


def schema_errors(tmp_path: Path, metadata: str, strict: bool) -> str:
    meta_dir = tmp_path / ".doc_gen" / "metadata"
    meta_dir.mkdir(parents=True)
    (meta_dir / "s3_metadata.yaml").write_text(metadata)
    errors = validate_metadata(tmp_path, strict, MetadataErrors())
    return str(errors) if len(errors) else ""


@pytest.mark.parametrize("strict", [True, False])
@pytest.mark.parametrize(
    "metadata",
    [
        pytest.param(FULL, id="new-feature"),
        # An established feature gets a description only.
        pytest.param(entry(description=DESCRIPTION), id="description-only"),
        pytest.param(entry(), id="no-feature-fields"),
    ],
)
def test_schema_accepts_finalizer_output(tmp_path, metadata, strict):
    assert schema_errors(tmp_path, metadata, strict) == ""


@pytest.mark.parametrize(
    "fields,expected",
    [
        pytest.param(
            dict(available_since='"2026-6-16"', available_since_version=VERSIONS),
            "available_since",
            id="date-not-iso",
        ),
        pytest.param(
            dict(
                available_since='"2026-06-16"',
                available_since_version='{"Python": {"version": "1.43.31", "basis": "guess"}}',
            ),
            "basis",
            id="unknown-basis",
        ),
        pytest.param(
            dict(
                available_since='"2026-06-16"',
                available_since_version=VERSIONS,
                introduced_operations='["s3:PutObjectAnnotation"]',
            ),
            "introduced_operations",
            id="operation-not-a-model-name",
        ),
        pytest.param(
            dict(description='"Object annotations let you attach metadata"'),
            "description",
            id="description-no-end-punctuation",
        ),
        pytest.param(
            dict(description='"AWS object annotations let you attach metadata."'),
            'non-entity usage of "AWS"',
            id="description-bare-aws",
        ),
        pytest.param(
            dict(availability_description='"Object annotations."'),
            "availability_description",
            id="retired-key",
        ),
    ],
)
def test_strict_schema_rejects(tmp_path, fields, expected):
    errors = schema_errors(tmp_path, entry(**fields), strict=True)
    assert expected in errors


def test_parse_reads_all_fields(tmp_path):
    path = tmp_path / "s3_metadata.yaml"
    path.write_text(FULL)
    doc_gen = DocGen.from_root(tmp_path)
    doc_gen.process_metadata(path)
    example = doc_gen.examples["s3_Scenario_ObjectAnnotations"]

    assert example.description == yaml.safe_load(DESCRIPTION)
    assert example.available_since == "2026-06-16"
    assert example.available_since_version == {
        "Python": AvailabilityVersion(version="1.43.31", major="3", basis="exact"),
        "PowerShell": AvailabilityVersion(version="5.0.0", major="5", basis="at_least"),
    }
    assert example.introduced_operations == [
        "PutObjectAnnotation",
        "GetObjectAnnotation",
    ]


def test_writer_keeps_fields(tmp_path):
    path = tmp_path / "s3_metadata.yaml"
    path.write_text(FULL)
    doc_gen = DocGen.from_root(tmp_path)
    doc_gen.process_metadata(path)
    examples = {
        "s3_Scenario_ObjectAnnotations": doc_gen.examples[
            "s3_Scenario_ObjectAnnotations"
        ]
    }

    [written] = prepare_write(examples).values()
    rewritten = yaml.safe_load(written)["s3_Scenario_ObjectAnnotations"]
    original = yaml.safe_load(FULL)["s3_Scenario_ObjectAnnotations"]

    for key in (
        "description",
        "available_since",
        "available_since_version",
        "introduced_operations",
    ):
        assert rewritten[key] == original[key]


def test_writer_omits_unset_version_subfields():
    example = _example(["Python"], "2026-06-16", {"Python": "1.43.31"})
    [written] = prepare_write({example.id: example}).values()
    rewritten = yaml.safe_load(written)[example.id]
    assert rewritten["available_since_version"] == {"Python": {"version": "1.43.31"}}
    assert "description" not in rewritten
    assert "introduced_operations" not in rewritten


def _example(
    languages: List[str],
    available_since: Optional[str],
    versions: Dict[str, str],
    operations: Optional[List[str]] = None,
    description: Optional[str] = None,
) -> Example:
    return Example(
        id="s3_Scenario_ObjectAnnotations",
        file=Path("s3_metadata.yaml"),
        category="Scenarios",
        languages={
            name: Language(name=name, property=name.lower(), versions=[])
            for name in languages
        },
        services={"s3": {"PutObjectAnnotation"}},
        description=description,
        available_since=available_since,
        available_since_version={
            lang: AvailabilityVersion(version=v) for lang, v in versions.items()
        },
        introduced_operations=operations or [],
    )


@pytest.mark.parametrize(
    "languages,available_since,versions,operations,description,expected",
    [
        pytest.param(
            ["Python"],
            "2026-06-16",
            {"Python": "1.43.31"},
            ["Op"],
            "A feature.",
            [],
            id="complete",
        ),
        # The version table covers every SDK that supports the feature, so
        # entries for SDKs the example is not published in are allowed.
        pytest.param(
            ["Python"],
            "2026-06-16",
            {"Python": "1.43.31", "JavaScript": "3.1070.0", ".NET": "4.0.25.0"},
            None,
            None,
            [],
            id="extra-sdks-allowed",
        ),
        pytest.param(
            ["Python", "Java"],
            "2026-06-16",
            {"Python": "1.43.31"},
            None,
            None,
            [metadata_errors.AvailabilityVersionLanguageMismatch],
            id="published-language-without-version",
        ),
        pytest.param(
            ["Python"],
            None,
            {"Python": "1.43.31"},
            None,
            None,
            [metadata_errors.AvailabilityMissingDate],
            id="versions-without-date",
        ),
        pytest.param(
            ["Python"],
            None,
            {},
            ["Op"],
            None,
            [metadata_errors.AvailabilityMissingDate],
            id="operations-without-date",
        ),
        pytest.param(
            ["Python"],
            "2026-06-16",
            {},
            None,
            None,
            [metadata_errors.AvailabilityMissingVersions],
            id="date-without-versions",
        ),
        # An established feature: description only, no availability facts.
        pytest.param(
            ["Python"], None, {}, None, "A feature.", [], id="description-only"
        ),
        pytest.param(["Python"], None, {}, None, None, [], id="no-feature-fields"),
    ],
)
def test_semantic_validation(
    languages, available_since, versions, operations, description, expected
):
    example = _example(languages, available_since, versions, operations, description)
    errors = MetadataErrors()
    example.validate(errors, {"s3"}, Path("."))
    assert [type(e) for e in errors] == expected
