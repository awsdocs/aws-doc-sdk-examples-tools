# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

import logging
from pathlib import Path

import pytest
import yaml

from .doc_gen import DocGen
from .metadata_errors import DuplicateYamlKey, MetadataErrors
from .yaml_duplicates import DuplicateKey, load_yaml_with_duplicates


def test_root_duplicate_differing():
    content = "a: 1\nb: 2\na: 3\n"
    data, dups = load_yaml_with_duplicates(content)
    assert data == yaml.safe_load(content) == {"a": 3, "b": 2}
    assert dups == [
        DuplicateKey(key="a", path="", first=(1, 1), again=(3, 1), identical=False)
    ]


def test_nested_duplicate_identical():
    content = "x:\n  y: 1\n  z: 2\n  y: 1\n"
    data, dups = load_yaml_with_duplicates(content)
    assert data == {"x": {"y": 1, "z": 2}}
    assert dups == [
        DuplicateKey(key="y", path="x", first=(2, 3), again=(4, 3), identical=True)
    ]


def test_duplicate_in_list_item():
    content = "x:\n  versions:\n    - k: 1\n      k: 2\n    - k: 3\n"
    data, dups = load_yaml_with_duplicates(content)
    assert data == {"x": {"versions": [{"k": 2}, {"k": 3}]}}
    assert dups == [
        DuplicateKey(
            key="k", path="x.versions[0]", first=(3, 7), again=(4, 7), identical=False
        )
    ]


def test_duplicate_in_flow_mapping():
    content = "x:\n  services:\n    kms: {ListGrants, CreateKey, ListGrants}\n"
    data, dups = load_yaml_with_duplicates(content)
    assert data == yaml.safe_load(content)
    assert dups == [
        DuplicateKey(
            key="ListGrants",
            path="x.services.kms",
            first=(3, 11),
            again=(3, 34),
            identical=True,
        )
    ]


def test_nested_values_compared_deeply():
    differ = "a:\n  b: [1, 2]\na:\n  b: [1, 3]\n"
    same = "a:\n  b: [1, 2]\na:\n  b: [1, 2]\n"
    assert [d.identical for d in load_yaml_with_duplicates(differ)[1]] == [False]
    assert [d.identical for d in load_yaml_with_duplicates(same)[1]] == [True]


def test_every_duplicate_is_reported():
    content = "a: 1\na: 2\na: 2\nb:\n  c: 1\n  c: 1\n"
    _, dups = load_yaml_with_duplicates(content)
    assert [(d.key, d.path, d.first, d.again, d.identical) for d in dups] == [
        ("a", "", (1, 1), (2, 1), False),
        ("a", "", (1, 1), (3, 1), False),
        ("c", "b", (5, 3), (6, 3), True),
    ]


def test_keys_that_load_to_the_same_value():
    content = "true: 1\nyes: 1\n"
    data, dups = load_yaml_with_duplicates(content)
    assert data == yaml.safe_load(content) == {True: 1}
    assert [(d.key, d.first, d.again, d.identical) for d in dups] == [
        ("yes", (1, 1), (2, 1), True)
    ]


def test_merge_key_override_is_not_a_duplicate():
    content = "base: &b {x: 1, y: 2}\nother:\n  <<: *b\n  x: 3\n"
    data, dups = load_yaml_with_duplicates(content)
    assert data == yaml.safe_load(content)
    assert data["other"] == {"x": 3, "y": 2}
    assert dups == []


def test_self_referential_duplicate_values():
    content = "a: &a [*a]\na: &c [*c]\n"
    data, dups = load_yaml_with_duplicates(content)
    loaded = yaml.safe_load(content)
    assert list(data) == list(loaded) == ["a"]
    assert data["a"][0] is data["a"]
    assert len(data["a"]) == 1
    assert dups == [
        DuplicateKey(key="a", path="", first=(1, 1), again=(2, 1), identical=False)
    ]


def test_clean_file_unchanged():
    content = (
        "ex_One:\n"
        "  title: One\n"
        "  languages:\n"
        "    Python:\n"
        "      versions:\n"
        "        - sdk_version: 3\n"
        "          excerpts:\n"
        "            - snippet_tags: [a, b]\n"
        "  services:\n"
        "    ex: {One}\n"
    )
    data, dups = load_yaml_with_duplicates(content)
    assert dups == []
    assert data == yaml.safe_load(content)
    assert list(data["ex_One"].keys()) == ["title", "languages", "services"]


def test_empty_document():
    assert load_yaml_with_duplicates("") == (None, [])


def test_malformed_yaml_raises_like_safe_load():
    content = "a: [1, 2\nb: 3\n"
    with pytest.raises(yaml.YAMLError) as expected:
        yaml.safe_load(content)
    with pytest.raises(type(expected.value)):
        load_yaml_with_duplicates(content)


DUPLICATE_KEYS_METADATA = """\
medical-imaging_TestExample:
  title: First title
  title_abbrev: Test
  synopsis: test the thing.
  category: Usage
  title: Second title
  languages:
    Java:
      versions:
        - sdk_version: 2
          github: test_path
          block_content: test block
          block_content: test block
  services:
    medical-imaging: {CreateDatastore, CreateDatastore}
"""


def doc_gen_for_test_resources() -> DocGen:
    return DocGen(Path(), MetadataErrors()).for_root(
        Path(__file__).parent / "test_resources", incremental=False
    )


def duplicate_errors(doc_gen: DocGen):
    return [e for e in doc_gen.errors if isinstance(e, DuplicateYamlKey)]


def test_duplicate_keys_conflicting_is_error(tmp_path: Path):
    path = tmp_path / "dups_metadata.yaml"
    path.write_text(DUPLICATE_KEYS_METADATA)
    doc_gen = doc_gen_for_test_resources()
    doc_gen.process_metadata(path)

    dups = [e for e in duplicate_errors(doc_gen) if e.key == "title"]
    assert len(dups) == 1
    error = dups[0]
    assert error.file == path
    assert error.id == "medical-imaging_TestExample"
    assert not error.identical
    text = str(error)
    assert str(path) in text
    assert "'title'" in text
    assert "2:3" in text
    assert "6:3" in text
    assert "copies differ" in text
    # The loaded example is the same as before: the last copy wins.
    assert doc_gen.examples["medical-imaging_TestExample"].title == "Second title"


def test_duplicate_keys_identical_is_error(tmp_path: Path, caplog):
    path = tmp_path / "dups_metadata.yaml"
    path.write_text(DUPLICATE_KEYS_METADATA)
    doc_gen = doc_gen_for_test_resources()
    with caplog.at_level(logging.WARNING):
        doc_gen.process_metadata(path)

    errors = duplicate_errors(doc_gen)
    assert [e.key for e in errors] == ["title", "block_content", "CreateDatastore"]
    identical = [e for e in errors if e.identical]
    assert [e.key for e in identical] == ["block_content", "CreateDatastore"]
    messages = [str(e) for e in identical]
    assert all(str(path) in m for m in messages)
    assert all("copies are identical" in m for m in messages)
    assert "12:11" in messages[0] and "13:11" in messages[0]
    assert "15:23" in messages[1] and "15:40" in messages[1]
    assert not [r for r in caplog.records if r.levelno >= logging.WARNING]


def test_no_duplicate_keys_no_reports(caplog):
    doc_gen = doc_gen_for_test_resources()
    with caplog.at_level(logging.WARNING):
        doc_gen.process_metadata(doc_gen.root / "valid_metadata.yaml")
    assert not [e for e in doc_gen.errors if isinstance(e, DuplicateYamlKey)]
    assert not [r for r in caplog.records if r.levelno >= logging.WARNING]
    assert len(doc_gen.examples) == 1
