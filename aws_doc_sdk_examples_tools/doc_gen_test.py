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
from .services import Service
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
            ),
            DocGen(
                root=Path("/b"),
                errors=MetadataErrors(),
                sdks={
                    "b": Sdk(name="b", guide="guide_b", property="b_prop", versions=[])
                },
            ),
            DocGen(
                root=Path("/a"),
                errors=MetadataErrors(),
                sdks={
                    "a": Sdk(name="a", guide="guide_a", property="a_prop", versions=[]),
                    "b": Sdk(name="b", guide="guide_b", property="b_prop", versions=[]),
                },
            ),
        )
    ],
)
def test_merge(a: DocGen, b: DocGen, d: DocGen):
    a.merge(b)
    assert a == d


@pytest.fixture
def sample_doc_gen() -> DocGen:
    metadata_errors = MetadataErrors()
    metadata_errors._errors = [MetadataError(file="filea.txt", id="Error a")]
    return DocGen(
        root=Path("/test/root"),
        errors=metadata_errors,
        prefix="test_prefix",
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
                long="Amazon S3",
                short="S3",
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


def test_doc_gen_encoder(sample_doc_gen: DocGen):
    encoded = json.dumps(sample_doc_gen, cls=DocGenEncoder)
    decoded = json.loads(encoded)

    # Verify that the root path is not included in the encoded output
    assert "root" not in decoded or decoded["root"] is None

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
    assert decoded["services"]["s3"]["long"] == "Amazon S3"
    assert decoded["services"]["s3"]["short"] == "S3"

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
