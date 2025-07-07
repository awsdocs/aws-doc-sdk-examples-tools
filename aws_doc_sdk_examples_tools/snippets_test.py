# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

import pytest
from pathlib import Path

from aws_doc_sdk_examples_tools import snippets
from aws_doc_sdk_examples_tools.fs import RecordFs
from aws_doc_sdk_examples_tools.metadata import Example, Language, Version, Excerpt
from aws_doc_sdk_examples_tools.metadata_errors import MetadataErrors


@pytest.mark.parametrize(
    "file_contents,expected_error_count",
    [
        (
            "snippet" + "-start:[this.is.a.snippet.tag]\n"
            "This is not code.\n"
            "snippet" + "-end:[this.is.a.snippet.tag]",
            0,
        ),
        (
            "snippet" + "-start:[this.is.a.snippet.tag]\n"
            "This is not code.\n"
            "snippet" + "-end:[this.is.a.different.snippet.tag]",
            2,
        ),
        ("snippet" + "-start:[this.is.a.snippet.tag]\n" "This is not code.", 1),
        ("This is not code.\n" "snippet" + "-end:[this.is.a.snippet.tag]", 1),
        (
            "snippet" + "-start:[this.is.a.snippet.tag]\n"
            "snippet" + "-start:[this.is.a.different.snippet.tag]\n"
            "This is not code.\n"
            "snippet" + "-end:[this.is.a.snippet.tag]\n"
            "snippet" + "-end:[this.is.a.different.snippet.tag]\n",
            0,
        ),
        (
            "snippet" + "-start:[this.is.a.snippet.tag]\n"
            "snippet" + "-start:[this.is.a.different.snippet.tag]\n"
            "This is not code.\n"
            "snippet" + "-end:[this.is.a.different.snippet.tag]\n"
            "snippet" + "-end:[this.is.a.snippet.tag]\n",
            0,
        ),
        (
            "snippet" + "-start:[this.is.a.snippet.tag]\n"
            "This is not code.\n"
            "snippet" + "-end:[this.is.a.snippet.tag.with.extra.stuff]\n",
            2,
        ),
        (
            "snippet" + "-start:[this.is.a.snippet.tag]\n"
            "snippet" + "-start:[this.is.a.snippet.tag]\n"
            "This is not code.\n"
            "snippet" + "-end:[this.is.a.snippet.tag]\n",
            1,
        ),
        (
            "snippet" + "-start:[this.is.a.snippet.tag]\n"
            "This is not code.\n"
            "snippet" + "-end:[this.is.a.snippet.tag]\n"
            "snippet" + "-end:[this.is.a.snippet.tag]\n",
            1,
        ),
    ],
)
def test_verify_snippet_start_end(file_contents: str, expected_error_count: int):
    """Test that various kinds of mismatched snippet-start and -end tags are
    counted correctly as errors."""
    _, errors = snippets.parse_snippets(file_contents.split("\n"), Path("test"), "")
    error_count = len(errors)
    assert error_count == expected_error_count


def test_strip_snippet_tags():
    assert ["Line A", "Line C"] == snippets.strip_snippet_tags(
        [
            "Line A",
            "# snippet-start:[line b]",
            "Line C",
            "# snippet-end:[line d]",
            "line E # snippet-end",
        ]
    )


def test_strip_spdx_header():
    assert ["Line A", "Line B"] == snippets.strip_spdx_header(
        [
            "# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.",
            "# SPDX-License-Identifier: Apache-2.0",
            "Line A",
            "Line B",
        ]
    )
    assert ["Line A", "Line B"] == snippets.strip_spdx_header(
        [
            "# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.",
            "# SPDX-License-Identifier: Apache-2.0",
            "",
            "Line A",
            "Line B",
        ]
    )

    assert [] == snippets.strip_spdx_header([])


class TestFindSnippetsFs:
    """Test find_snippets with filesystem abstraction."""

    def test_find_snippets_with_recordfs(self):
        """Test find_snippets using RecordFs."""
        fs = RecordFs(
            {
                Path(
                    "/project/test.py"
                ): """# snippet-start:[example.hello]
def hello():
    print("Hello, World!")
# snippet-end:[example.hello]
"""
            }
        )

        snippet_dict, errors = snippets.find_snippets(
            Path("/project/test.py"), "", fs=fs
        )

        assert len(errors) == 0
        assert len(snippet_dict) == 1
        assert "example.hello" in snippet_dict
        snippet = snippet_dict["example.hello"]
        assert snippet.id == "example.hello"
        assert "def hello():" in snippet.code

    def test_find_snippets_missing_file_graceful(self):
        """Test find_snippets behavior with missing files."""
        fs = RecordFs({})

        snippet_dict, errors = snippets.find_snippets(
            Path("/project/missing.py"), "", fs=fs
        )

        # Missing files generate errors (not handled gracefully)
        assert len(snippet_dict) == 0
        assert len(errors) == 1  # Should have a FileReadError


class TestCollectSnippetsFs:
    """Test collect_snippets with filesystem abstraction."""

    def test_collect_snippets_with_recordfs(self):
        """Test collect_snippets using RecordFs."""
        fs = RecordFs(
            {
                Path(
                    "/project/src/file1.py"
                ): """# snippet-start:[example1]
def example1():
    pass
# snippet-end:[example1]
""",
                Path(
                    "/project/src/file2.py"
                ): """# snippet-start:[example2]
def example2():
    pass
# snippet-end:[example2]
""",
            }
        )

        snippet_dict, errors = snippets.collect_snippets(Path("/project/src"), fs=fs)

        assert len(errors) == 0
        assert len(snippet_dict) == 2
        assert "example1" in snippet_dict
        assert "example2" in snippet_dict


class TestCollectSnippetFilesFs:
    """Test collect_snippet_files with filesystem abstraction."""

    def test_collect_snippet_files_with_recordfs(self):
        """Test collect_snippet_files using RecordFs."""
        fs = RecordFs({Path("/project/example.py"): "print('Hello, World!')\n"})

        example = Example(
            id="test_example",
            file=None,
            languages={
                "python": Language(
                    name="python",
                    property="python",
                    versions=[
                        Version(
                            sdk_version="3",
                            excerpts=[
                                Excerpt(
                                    description="Test excerpt",
                                    snippet_tags=[],
                                    snippet_files=["example.py"],
                                )
                            ],
                        )
                    ],
                )
            },
        )

        snippet_dict = {}
        errors = MetadataErrors()

        snippets.collect_snippet_files(
            [example], snippet_dict, "", errors, Path("/project"), fs=fs
        )

        assert len(errors) == 0
        assert len(snippet_dict) == 1
        assert "example.py" in snippet_dict
        snippet = snippet_dict["example.py"]
        assert snippet.file == "example.py"
        assert "Hello, World!" in snippet.code

    def test_collect_snippet_files_missing_file_error(self):
        """Test collect_snippet_files properly reports missing files as errors."""
        fs = RecordFs({})  # Empty filesystem

        example = Example(
            id="test_example",
            file=None,
            languages={
                "python": Language(
                    name="python",
                    property="python",
                    versions=[
                        Version(
                            sdk_version="3",
                            excerpts=[
                                Excerpt(
                                    description="Test excerpt",
                                    snippet_tags=[],
                                    snippet_files=["missing.py"],
                                )
                            ],
                        )
                    ],
                )
            },
        )

        snippet_dict = {}
        errors = MetadataErrors()

        snippets.collect_snippet_files(
            [example], snippet_dict, "", errors, Path("/project"), fs=fs
        )

        # Missing snippet files should generate errors (unlike find_snippets)
        assert len(errors) == 1
        assert len(snippet_dict) == 0
