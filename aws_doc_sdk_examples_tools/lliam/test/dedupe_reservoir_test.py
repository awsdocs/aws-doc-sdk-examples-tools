from collections import Counter
from pathlib import Path

from aws_doc_sdk_examples_tools.metadata import Example
from aws_doc_sdk_examples_tools.lliam.service_layer.dedupe_reservoir import (
    make_abbrev,
    example_in_packages,
    reset_abbrev_count,
    dedupe_examples,
)


def test_make_abbrev_continues_numbering():
    """Test that numbering continues from existing numbered titles."""
    counter = Counter({"Some abbrev": 2})
    example = Example(id="test", file=Path(), languages={}, title_abbrev="Some abbrev")
    result = make_abbrev(example, counter)

    assert result == "Some abbrev (3)"


def test_make_abbrev_first_occurrence():
    """Test that first occurrence doesn't get numbered."""
    counter = Counter()
    example = Example(id="test", file=Path(), languages={}, title_abbrev="New abbrev")
    result = make_abbrev(example, counter)

    assert result == "New abbrev"
    assert counter["New abbrev"] == 1


def test_example_in_packages_no_packages():
    """Test that example is included when no packages specified."""
    example = Example(id="test", file=Path("test_metadata.yaml"), languages={})
    result = example_in_packages(example, [])

    assert result is True


def test_example_in_packages_matching_package():
    """Test that example is included when package matches."""
    example = Example(id="test", file=Path("pkg1_metadata.yaml"), languages={})
    result = example_in_packages(example, ["pkg1", "pkg2"])

    assert result is True


def test_example_in_packages_non_matching_package():
    """Test that example is excluded when package doesn't match."""
    example = Example(id="test", file=Path("pkg3_metadata.yaml"), languages={})
    result = example_in_packages(example, ["pkg1", "pkg2"])

    assert result is False


def test_build_abbrev_counter():
    """Test building counter from examples with existing numbered titles."""
    examples = {
        "1": Example(id="1", file=Path(), languages={}, title_abbrev="Test (1)"),
        "2": Example(id="2", file=Path(), languages={}, title_abbrev="Test (2)"),
        "3": Example(id="3", file=Path(), languages={}, title_abbrev="Other"),
        "4": Example(id="4", file=Path(), languages={}, title_abbrev="Test"),
    }

    result = reset_abbrev_count(examples)

    assert result["1"].title_abbrev == "Test"
    assert result["2"].title_abbrev == "Test"
    assert result["3"].title_abbrev == "Other"
    assert result["4"].title_abbrev == "Test"


def test_build_abbrev_counter_empty():
    """Test building counter from empty examples list."""
    result = reset_abbrev_count({})

    assert len(result) == 0


def test_dedupe_examples():
    """Test deduping examples with existing numbered titles."""
    examples = {
        "ex1": Example(
            id="ex1",
            file=Path("pkg1_metadata.yaml"),
            languages={},
            title_abbrev="Test (2) (2)",
        ),
        "ex2": Example(
            id="ex2",
            file=Path("pkg1_metadata.yaml"),
            languages={},
            title_abbrev="Test (3) (3) (3)",
        ),
        "ex3": Example(
            id="ex3", file=Path("pkg1_metadata.yaml"), languages={}, title_abbrev="Test"
        ),
        "ex4": Example(
            id="ex4", file=Path("pkg1_metadata.yaml"), languages={}, title_abbrev="Test"
        ),
        "ex5": Example(
            id="ex5", file=Path("pkg1_metadata.yaml"), languages={}, title_abbrev="Test"
        ),
        "ex6": Example(
            id="ex6", file=Path("pkg2_metadata.yaml"), languages={}, title_abbrev="Test"
        ),
    }

    result = dedupe_examples(examples, [])

    assert len(result) == 6
    title_abbrevs = sorted(
        [ex.title_abbrev for ex in result.values() if ex.title_abbrev]
    )
    assert title_abbrevs == [
        "Test",
        "Test (2)",
        "Test (3)",
        "Test (4)",
        "Test (5)",
        "Test (6)",
    ]
