# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

"""
Test for that parts of DocGen that aren't file I/O.
"""

import pytest
from pathlib import Path
import json

from .metadata_errors import MetadataErrors, MetadataError
from .doc_gen import DocGen, DocGenEncoder
from .sdks import Sdk, SdkVersion
from .services import Service, ServiceExpanded
from .snippets import Snippet


@pytest.mark.parametrize(
    ["a", "b", "d"],
    [
        (
            DocGen(
                root=Path("/a"),
                errors=MetadataErrors(),
                sdks={
                    "a": Sdk(name="a", guide="guide_a", property="a_prop", versions=[])
                },
                services={
                    "x": Service(long="AWS X", short="X", sort="aws x", version=1)
                },
            ),
            DocGen(
                root=Path("/b"),
                errors=MetadataErrors(),
                sdks={
                    "b": Sdk(name="b", guide="guide_b", property="b_prop", versions=[])
                },
                services={
                    "y": Service(long="AWS Y", short="Y", sort="aws y", version=1)
                },
            ),
            DocGen(
                root=Path("/a"),
                errors=MetadataErrors(),
                sdks={
                    "a": Sdk(name="a", guide="guide_a", property="a_prop", versions=[]),
                    "b": Sdk(name="b", guide="guide_b", property="b_prop", versions=[]),
                },
                services={
                    "x": Service(long="AWS X", short="X", sort="aws x", version=1),
                    "y": Service(long="AWS Y", short="Y", sort="aws y", version=1),
                },
            ),
        )
    ],
)
def test_merge(a: DocGen, b: DocGen, d: DocGen):
    a.merge(b)
    assert a == d


def test_incremental():
    errors = MetadataErrors()
    doc_gen = DocGen(Path(), errors).for_root(
        Path(__file__).parent / "test_resources", incremental=False
    )
    assert len(doc_gen.examples) == 0
    doc_gen.process_metadata(doc_gen.root / "awsentity_metadata.yaml")
    assert len(doc_gen.examples) == 5
    doc_gen.process_metadata(doc_gen.root / "valid_metadata.yaml")
    assert len(doc_gen.examples) == 6


@pytest.fixture
def sample_doc_gen() -> DocGen:
    metadata_errors = MetadataErrors()
    metadata_errors._errors = [MetadataError(file=Path("filea.txt"), id="Error a")]
    return DocGen(
        root=Path("/test/root"),
        errors=metadata_errors,
        prefix="test_prefix",
        entities={"&S3long;": "Amazon Simple Storage Service", "&S3;": "Amazon S3"},
        sdks={
            "python": Sdk(
                name="python",
                versions=[
                    SdkVersion(version=1, long="Python SDK v1", short="Python v1")
                ],
                guide="Python Guide",
                property="python",
            )
        },
        services={
            "s3": Service(
                long="&S3long;",
                short="&S3;",
                expanded=ServiceExpanded(
                    long="Amazon Simple Storage Service", short="Amazon S3"
                ),
                sort="Amazon S3",
                version="2006-03-01",
            )
        },
        snippets={
            "test_snippet": Snippet(
                id="test_snippet",
                file="test.py",
                line_start=1,
                line_end=5,
                code="print('Hello, World!')",
            )
        },
        snippet_files={"test.py"},
        examples={},
        cross_blocks={"test_block"},
    )


def test_expand_entities(sample_doc_gen: DocGen):
    expanded, errors = sample_doc_gen.expand_entities("Hello &S3;")
    assert expanded == "Hello Amazon S3"
    assert not errors


def test_doc_gen_encoder(sample_doc_gen: DocGen):
    encoded = json.dumps(sample_doc_gen, cls=DocGenEncoder)
    decoded = json.loads(encoded)

    # Verify that the root path is not included in the encoded output
    assert "/test/root" not in decoded
    assert decoded["root"] == "root"

    # Verify SDK information
    assert "sdks" in decoded
    assert "python" in decoded["sdks"]
    assert decoded["sdks"]["python"]["name"] == "python"
    assert decoded["sdks"]["python"]["guide"] == "Python Guide"
    assert decoded["sdks"]["python"]["versions"][0]["version"] == 1
    assert decoded["sdks"]["python"]["versions"][0]["long"] == "Python SDK v1"

    # Verify service information
    assert "services" in decoded
    assert "s3" in decoded["services"]
    assert decoded["services"]["s3"]["long"] == "&S3long;"
    assert decoded["services"]["s3"]["short"] == "&S3;"

    # Verify snippet information
    assert "snippets" in decoded
    assert "test_snippet" in decoded["snippets"]
    assert decoded["snippets"]["test_snippet"]["id"] == "test_snippet"
    assert decoded["snippets"]["test_snippet"]["file"] == "test.py"
    assert decoded["snippets"]["test_snippet"]["code"] == "print('Hello, World!')"

    # Verify snippet files
    assert "snippet_files" in decoded
    assert decoded["snippet_files"] == {"__set__": ["test.py"]}

    # Verify cross blocks
    assert "cross_blocks" in decoded
    assert decoded["cross_blocks"] == {"__set__": ["test_block"]}

    # Verify that errors are properly encoded
    assert "errors" in decoded
    assert decoded["errors"] == {
        "__metadata_errors__": [{"file": "filea.txt", "id": "Error a"}]
    }

    # Verify prefix
    assert decoded["prefix"] == "test_prefix"

    # Verify examples (empty in this case)
    assert "examples" in decoded
    assert decoded["examples"] == {}


def test_doc_gen_load_snippets():
    errors = MetadataErrors()
    doc_gen = DocGen(Path(), errors).for_root(
        Path(__file__).parent / "test_resources", incremental=False
    )
    doc_gen.process_metadata(doc_gen.root / "valid_metadata.yaml")
    doc_gen.collect_snippets()
    assert doc_gen.snippet_files == set(["snippet_file.txt"])
    assert doc_gen.snippets["snippet_file.txt"].code == "Line A\nLine C\n"
