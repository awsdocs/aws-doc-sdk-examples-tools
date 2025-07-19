from pathlib import Path
import pytest

from aws_doc_sdk_examples_tools.doc_gen import DocGen
from aws_doc_sdk_examples_tools.yaml_writer import (
    prepare_write,
    report_yaml_differences,
)


ROOT = Path(__file__).parent / "test_resources" / "doc_gen_test"


@pytest.fixture
def sample_doc_gen():
    return DocGen.from_root(ROOT)


def test_doc_gen(sample_doc_gen: DocGen):
    del sample_doc_gen.examples["sns_EntityFailures"]
    writes = prepare_write(sample_doc_gen.examples)
    assert writes

    writes = {
        Path(k.replace(str(ROOT), "")).as_posix().lstrip("/"): v
        for k, v in writes.items()
    }

    expected_writes = {
        ".doc_gen/metadata/aws_entity_metadata.yaml": """sns_EntitySuccesses:
  title: Title has &AWS; using an &AWS; SDK
  title_abbrev: Title Abbrev has &AWS; in it
  synopsis: this <programlisting>Synopsis programlisting has AWS in it.</programlisting>.
  synopsis_list:
  - Synopsis list code has <code>AWS</code> in it.
  category: Cat
  languages:
    Java:
      versions:
      - sdk_version: 1
        github: java/example_code/svc_EntityFailures
        excerpts:
        - description: This <emphasis><programlisting>Description programlisting has AWS in it</programlisting></emphasis> doesn't it.
          snippet_tags:
          - java.example_code.svc_EntityFailures.Test
  services:
    sns: {}
"""
    }

    assert writes == expected_writes


def test_report_yaml_differences_with_changes():
    """Test that report_yaml_differences correctly identifies added, removed, and modified files."""
    before = {
        "file1.yaml": {"key1": "value1"},
        "file2.yaml": {"key2": "value2"},
        "file3.yaml": {"key3": "value3"},
    }

    after = {
        "file1.yaml": {"key1": "changed_value"},  # Modified
        "file3.yaml": {"key3": "value3"},  # Unchanged
        "file4.yaml": {"key4": "value4"},  # Added
        # file2.yaml is removed
    }

    differences = report_yaml_differences(before, after)

    # Sort the differences for consistent comparison
    differences.sort()

    expected = [
        ("file1.yaml", "{'key1': 'value1'}\n\n---\n\n{'key1': 'changed_value'}"),
        ("file2.yaml", "removed"),
        ("file4.yaml", "added"),
    ]
    expected.sort()
    assert differences == expected


def test_report_yaml_differences_no_changes():
    """Test that report_yaml_differences returns an empty list when dictionaries are identical."""
    before = {"file1.yaml": {"key": "value"}}
    after = {"file1.yaml": {"key": "value"}}

    differences = report_yaml_differences(before, after)
    assert differences == []
