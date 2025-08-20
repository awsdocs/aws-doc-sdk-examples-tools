import pytest
from pathlib import Path

from aws_doc_sdk_examples_tools.doc_gen import DocGen
from aws_doc_sdk_examples_tools.metadata import Example
from aws_doc_sdk_examples_tools.lliam.service_layer.update_doc_gen import (
    update_examples,
)


@pytest.fixture
def doc_gen_tributary():
    """
    Fixture that returns a DocGen instance using the doc_gen_tributary_test as root.
    """
    tributary_root = (
        Path(__file__).parent.parent.parent
        / "test_resources"
        / "doc_gen_tributary_test"
    )
    doc_gen = DocGen.from_root(tributary_root)
    doc_gen.collect_snippets()
    return doc_gen


def smoke_test_doc_gen(doc_gen_tributary: DocGen):
    assert isinstance(doc_gen_tributary, DocGen)


def test_update_examples_title_abbrev(doc_gen_tributary: DocGen):
    """Test that title_abbrev is updated correctly with service_main suffix."""
    # Create an example with a title_abbrev to update
    update_example = Example(
        id="iam_policies_example",
        file=Path(),
        languages={},
        title_abbrev="Updated Title Abbrev",
    )

    # Update the examples
    update_examples(doc_gen_tributary, [update_example])

    # Verify title_abbrev was updated with the service_main suffix
    updated_example = doc_gen_tributary.examples["iam_policies_example"]
    assert (
        updated_example.title_abbrev
        == "Updated Title Abbrev (from 'AWS Account Management' guide)"
    )
