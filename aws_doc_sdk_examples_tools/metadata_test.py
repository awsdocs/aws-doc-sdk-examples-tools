# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

"""
This script contains tests that verify the examples loader finds appropriate errors
"""

import pytest
import yaml
from pathlib import Path
from typing import List, Set, Tuple

from . import metadata_errors
from .metadata_errors import MetadataErrors
from .metadata import (
    parse,
    Example,
    Url,
    Language,
    Version,
    Excerpt,
    idFormat,
)
from .doc_gen import DocGen
from .project_validator import ValidationConfig
from .sdks import Sdk
from .services import Service, ServiceExpanded


def load(
    path: Path, doc_gen: DocGen, blocks: Set[str] = set()
) -> Tuple[List[Example], metadata_errors.MetadataErrors]:
    root = Path(__file__).parent
    filename = root / "test_resources" / path
    with open(filename) as file:
        meta = yaml.safe_load(file)
    return parse(filename.name, meta, doc_gen.sdks, doc_gen.services, blocks)


SERVICES = {
    "ses": Service(
        long="&SESlong;",
        short="&SES;",
        expanded=ServiceExpanded(
            long="Amazon Simple Email Service (Amazon SES)", short="Amazon SES"
        ),
        sort="ses",
        version=1,
    ),
    "sns": Service(
        long="&SNSlong;",
        short="&SNS;",
        expanded=ServiceExpanded(
            long="Amazon Simple Notification Service (Amazon SNS)", short="Amazon SNS"
        ),
        sort="sns",
        version=1,
    ),
    "sqs": Service(
        long="&SQSlong;",
        short="&SQS;",
        expanded=ServiceExpanded(
            long="Amazon Simple Queue Service (Amazon SQS)", short="Amazon SQS"
        ),
        sort="sqs",
        version=1,
    ),
    "s3": Service(
        long="&S3long;",
        short="&S3;",
        expanded=ServiceExpanded(
            long="Amazon Simple Storage Service (Amazon S3)", short="Amazon S3"
        ),
        sort="s3",
        version=1,
    ),
    "autogluon": Service(
        long="AutoGluon Test",
        short="AG Test",
        expanded=ServiceExpanded(long="AutoGluon Test", short="AutoGluon Test"),
        sort="autogluon",
        version=1,
    ),
}
SDKS = {
    "C++": Sdk(name="C++", versions=[], guide="", property=""),
    "Java": Sdk(name="Java", versions=[], guide="", property=""),
    "JavaScript": Sdk(name="JavaScript", versions=[], guide="", property=""),
    "PHP": Sdk(name="PHP", versions=[], guide="", property=""),
}
DOC_GEN = DocGen(
    root=Path(),
    errors=metadata_errors.MetadataErrors(),
    validation=ValidationConfig(),
    services=SERVICES,
    sdks=SDKS,
)

GOOD_SINGLE_CPP = """
sns_DeleteTopic:
   title: Deleting an &SNS; topic
   title_abbrev: Deleting a topic
   synopsis: |-
     Shows how to delete an &SNS; topic.
   languages:
     C++:
       versions:
         - sdk_version: 1
           github: cpp/example_code/sns
           sdkguide: sdkguide/link
           excerpts:
             - description: test excerpt description
               snippet_tags:
                 - test.excerpt
   services:
     sns:
       ? Operation1
       ? Operation2
     ses: { Operation1, Operation2 }
     sqs:
"""


def test_parse():
    meta = yaml.safe_load(GOOD_SINGLE_CPP)
    parsed, errors = parse("test_cpp.yaml", meta, SDKS, SERVICES, set())
    assert len(errors) == 0
    assert len(parsed) == 1
    language = Language(
        name="C++",
        versions=[
            Version(
                sdk_version=1,
                github="cpp/example_code/sns",
                sdkguide="sdkguide/link",
                excerpts=[
                    Excerpt(
                        description="test excerpt description",
                        snippet_tags=["test.excerpt"],
                    )
                ],
            )
        ],
    )
    example = Example(
        file="test_cpp.yaml",
        id="sns_DeleteTopic",
        category="Cross",
        title="Deleting an &SNS; topic",
        title_abbrev="Deleting a topic",
        synopsis="Shows how to delete an &SNS; topic.",
        services={
            "sns": set(["Operation1", "Operation2"]),
            "ses": set(["Operation1", "Operation2"]),
            "sqs": set(),
        },
        languages={"C++": language},
    )
    assert parsed[0] == example


CROSS_META = """
cross_DeleteTopic:
  title: Delete Topic
  title_abbrev: delete topic
  category: Cross-service examples
  languages:
     Java:
       versions:
         - sdk_version: 3
           block_content: cross_DeleteTopic_block.xml
  services:
     sns:
"""


def test_parse_cross():
    meta = yaml.safe_load(CROSS_META)
    actual, errors = parse(
        "cross.yaml", meta, SDKS, SERVICES, set(["cross_DeleteTopic_block.xml"])
    )
    assert len(errors) == 0
    assert len(actual) == 1
    language = Language(
        name="Java",
        versions=[Version(sdk_version=3, block_content="cross_DeleteTopic_block.xml")],
    )
    example = Example(
        file="cross.yaml",
        id="cross_DeleteTopic",
        category="Cross-service examples",
        title="Delete Topic",
        title_abbrev="delete topic",
        synopsis="",
        services={"sns": set()},
        languages={"Java": language},
    )
    assert actual[0] == example


CURATED = """
autogluon_tabular_with_sagemaker_pipelines:
  title: AutoGluon Tabular with SageMaker Pipelines
  title_abbrev: AutoGluon Tabular with SageMaker Pipelines
  synopsis: use AutoGluon with SageMaker Pipelines.
  source_key: amazon-sagemaker-examples
  category: Curated examples
  languages:
     Java:
       versions:
         - sdk_version: 2
           block_content: block.xml
  services:
     s3:
"""


def test_parse_curated():
    meta = yaml.safe_load(CURATED)
    actual, errors = parse("curated.yaml", meta, SDKS, SERVICES, set(["block.xml"]))
    assert len(errors) == 0
    assert len(actual) == 1
    language = Language(
        name="Java",
        versions=[Version(sdk_version=2, block_content="block.xml")],
    )
    example = Example(
        id="autogluon_tabular_with_sagemaker_pipelines",
        file="curated.yaml",
        category="Curated examples",
        title="AutoGluon Tabular with SageMaker Pipelines",
        title_abbrev="AutoGluon Tabular with SageMaker Pipelines",
        source_key="amazon-sagemaker-examples",
        languages={"Java": language},
        services={"s3": set()},
        synopsis="use AutoGluon with SageMaker Pipelines.",
    )

    assert actual[0] == example


def test_verify_load_successful():
    actual, errors = load(Path("valid_metadata.yaml"), DOC_GEN, set(["test block"]))
    assert len(errors) == 0
    assert len(actual) == 1
    java = Language(
        name="Java",
        versions=[
            Version(
                sdk_version=2,
                github="javav2/example_code/sns",
                block_content="test block",
                excerpts=[],
                add_services={},
                sdkguide=None,
                more_info=[],
            ),
        ],
    )

    javascript = Language(
        name="JavaScript",
        versions=[
            Version(
                sdk_version=3,
                github=None,
                block_content=None,
                add_services={"s3": set()},
                excerpts=[
                    Excerpt(
                        description="Descriptive",
                        snippet_files=[],
                        snippet_tags=["javascript.snippet.tag"],
                    )
                ],
                sdkguide=None,
                more_info=[],
            ),
        ],
    )

    php = Language(
        name="PHP",
        versions=[
            Version(
                sdk_version=3,
                github="php/example_code/sns",
                sdkguide="php/sdkguide/link",
                block_content=None,
                excerpts=[
                    Excerpt(
                        description="Optional description.",
                        snippet_tags=[
                            "php.snippet.tag.1",
                            "php.snippet.tag.2",
                        ],
                        snippet_files=[],
                    )
                ],
                add_services={},
                more_info=[],
            )
        ],
    )

    languages = {
        "Java": java,
        "JavaScript": javascript,
        "PHP": php,
    }

    example = Example(
        file="valid_metadata.yaml",
        id="sns_TestExample",
        title="Check whether a phone number is opted out using an &AWS; SDK",
        title_abbrev="Check whether a phone number is opted out",
        synopsis="check whether a phone number is opted out using some of the &AWS; SDKs that are available.",
        synopsis_list=["Check the one thing.", "Do some other thing."],
        guide_topic=Url(title="Test guide topic title", url="test-guide/url"),
        category="Usage",
        service_main=None,
        languages=languages,
        services={"sns": set(), "sqs": set()},
    )
    assert actual[0] == example


@pytest.mark.parametrize(
    "filename,expected_errors",
    [
        (
            "empty_metadata.yaml",
            [
                metadata_errors.MissingField(
                    field="title",
                    file="empty_metadata.yaml",
                    id="sns_EmptyExample",
                ),
                metadata_errors.MissingField(
                    field="title_abbrev",
                    file="empty_metadata.yaml",
                    id="sns_EmptyExample",
                ),
                metadata_errors.MissingField(
                    field="languages",
                    file="empty_metadata.yaml",
                    id="sns_EmptyExample",
                ),
            ],
        ),
        (
            "errors_metadata.yaml",
            [
                metadata_errors.APIMustHaveOneServiceOneAction(
                    file="errors_metadata.yaml",
                    id="sqs_WrongServiceSlug",
                    svc_actions="",
                ),
                metadata_errors.UnknownLanguage(
                    language="Perl",
                    file="errors_metadata.yaml",
                    id="sqs_WrongServiceSlug",
                ),
                metadata_errors.InvalidSdkGuideStart(
                    file="errors_metadata.yaml",
                    id="sqs_WrongServiceSlug",
                    language="Perl",
                    guide="https://docs.aws.amazon.com/absolute/link-to-my-guide",
                ),
                metadata_errors.MissingBlockContentAndExcerpt(
                    file="errors_metadata.yaml",
                    id="sqs_WrongServiceSlug",
                    language="Perl",
                    sdk_version=None,
                ),
                metadata_errors.APIExampleCannotAddService(
                    file="errors_metadata.yaml",
                    id="sqs_WrongServiceSlug",
                    language="Perl",
                    sdk_version=None,
                ),
                metadata_errors.MissingField(
                    field="versions",
                    file="errors_metadata.yaml",
                    id="sqs_TestExample",
                    language="Java",
                ),
                metadata_errors.MissingBlockContentAndExcerpt(
                    file="errors_metadata.yaml",
                    id="sns_TestExample",
                    language="Java",
                    sdk_version=None,
                ),
                # example_errors.MissingSnippetTag(
                #     file="errors_metadata.yaml",
                #     id="sqs_TestExample",
                #     language="Java",
                #     sdk_version=2,
                #     tag="this.snippet.does.not.exist",
                # ),
                metadata_errors.UnknownService(
                    file="errors_metadata.yaml",
                    id="sns_TestExample2",
                    service="garbled",
                ),
                metadata_errors.InvalidGithubLink(
                    file="errors_metadata.yaml",
                    id="sns_TestExample2",
                    language="Java",
                    sdk_version=2,
                    link="github/link/to/README.md",
                ),
                metadata_errors.BlockContentAndExcerptConflict(
                    file="errors_metadata.yaml",
                    id="cross_TestExample_Versions",
                    language="Java",
                    sdk_version=None,
                ),
                metadata_errors.MissingCrossContent(
                    file="errors_metadata.yaml",
                    id="cross_TestExample_Missing",
                    language="Java",
                    sdk_version=None,
                    block="missing_block_content.xml",
                ),
                metadata_errors.NameFormat(
                    file="errors_metadata.yaml",
                    id="snsBadFormat",
                ),
                metadata_errors.MissingBlockContentAndExcerpt(
                    file="errors_metadata.yaml",
                    id="snsBadFormat",
                    language="Java",
                ),
            ],
        ),
        (
            "formaterror_metadata.yaml",
            [
                metadata_errors.NameFormat(
                    file="formaterror_metadata.yaml",
                    id="WrongNameFormat",
                ),
                metadata_errors.UnknownService(
                    file="formaterror_metadata.yaml",
                    id="cross_TestExample",
                    language="Java",
                    service="garbage",
                ),
            ],
        ),
    ],
)
def test_common_errors(
    filename: str, expected_errors: List[metadata_errors.MetadataError]
):
    _, actual = load(Path(filename), DOC_GEN, set(["test/block", "cross_block.xml"]))
    assert expected_errors == [*actual]


TEST_SERVICES = {"test": Service("test", "test", "test", "1")}


def test_idFormat():
    assert idFormat("serverless_Snippet", TEST_SERVICES)
    assert idFormat("test_Test", TEST_SERVICES)
    assert idFormat("cross_Cross", TEST_SERVICES)
    assert not idFormat("other_Other", TEST_SERVICES)
    assert not idFormat("test", TEST_SERVICES)


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


if __name__ == "__main__":
    pytest.main([__file__, "-vv"])
