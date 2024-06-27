# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

"""
Test for that parts of DocGen that aren't file I/O.
"""

import pytest
from pathlib import Path
import json

from .metadata_errors import MetadataErrors
from .doc_gen import DocGen, DocGenDecoder, DocGenEncoder
from .sdks import Sdk


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


def test_encode_decode_integrity():
    root = Path(__file__).parent
    filename = root / "test_resources" / "serialized_doc_gen.json"

    with open(filename, "r") as serialized:
        serialized_str = serialized.read()
        decoded = json.loads(serialized_str, cls=DocGenDecoder)
        encoded = json.dumps(decoded, cls=DocGenEncoder)
        re_decoded = json.loads(encoded, cls=DocGenDecoder)

        assert decoded == re_decoded
