# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

"""
Test for that parts of DocGen that aren't file I/O.
"""

import pytest
from pathlib import Path

from .metadata_errors import MetadataErrors
from .doc_gen import DocGen
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
