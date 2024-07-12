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
from .metadata_errors import MetadataErrors, ExampleMergeConflict
from .metadata import (
    parse,
    DocFilenames,
    SDKVersion,
    SDKLanguage,
    SDKPages,
    Example,
    Url,
    Language,
    Version,
    Excerpt,
    check_id_format,
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
    with filename.open() as file:
        meta = yaml.safe_load(file)
    return parse(
        filename, meta, doc_gen.sdks, doc_gen.services, blocks, doc_gen.validation
    )


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
    "C++": Sdk(name="C++", versions=[], guide="", property="cpp"),
    "Java": Sdk(name="Java", versions=[], guide="", property="java"),
    "JavaScript": Sdk(name="JavaScript", versions=[], guide="", property="javascript"),
    "PHP": Sdk(name="PHP", versions=[], guide="", property="php"),
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
    parsed, errors = parse(
        Path("test_cpp.yaml"), meta, SDKS, SERVICES, set(), DOC_GEN.validation
    )
    assert len(errors) == 0
    assert len(parsed) == 1
    language = Language(
        name="C++",
        property="cpp",
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
        file=Path("test_cpp.yaml"),
        id="sns_DeleteTopic",
        category="Cross",
        services={
            "sns": set(["Operation1", "Operation2"]),
            "ses": set(["Operation1", "Operation2"]),
            "sqs": set(),
        },
        doc_filenames=DocFilenames(
            service_pages={
                "sns": "https://docs.aws.amazon.com/code-library/latest/ug/sns_example_sns_DeleteTopic_section.html",
                "sqs": "https://docs.aws.amazon.com/code-library/latest/ug/sqs_example_sns_DeleteTopic_section.html",
                "ses": "https://docs.aws.amazon.com/code-library/latest/ug/ses_example_sns_DeleteTopic_section.html",
            },
            sdk_pages={
                "cpp": {
                    1: SDKVersion(
                        actions_scenarios={
                            "sns": "https://docs.aws.amazon.com/code-library/latest/ug/cpp_1_sns_code_examples.html#scenarios",
                            "sqs": "https://docs.aws.amazon.com/code-library/latest/ug/cpp_1_sqs_code_examples.html#scenarios",
                            "ses": "https://docs.aws.amazon.com/code-library/latest/ug/cpp_1_ses_code_examples.html#scenarios",
                        }
                    )
                }
            },
        ),
        languages={"C++": language},
    )
    assert parsed[0] == example


STRICT_TITLE_META = """
sns_GoodOne:
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
     sns: {GoodOne}
sns_GoodScenario:
   title: Scenario title
   title_abbrev: Scenario title abbrev
   synopsis: scenario synopsis.
   category: Scenarios
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
     sns: {GoodOne}
"""


def test_parse_strict_titles():
    meta = yaml.safe_load(STRICT_TITLE_META)
    parsed, errors = parse(
        Path("test_cpp.yaml"),
        meta,
        SDKS,
        SERVICES,
        set(),
        ValidationConfig(strict_titles=True),
    )
    assert len(errors) == 0
    assert len(parsed) == 2
    language = Language(
        name="C++",
        property="cpp",
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
    example_action = Example(
        file=Path("test_cpp.yaml"),
        id="sns_GoodOne",
        category="Api",
        services={
            "sns": {"GoodOne"},
        },
        doc_filenames=DocFilenames(
            service_pages={
                "sns": "https://docs.aws.amazon.com/code-library/latest/ug/sns_example_sns_GoodOne_section.html",
            },
            sdk_pages={
                "cpp": {
                    1: SDKVersion(
                        actions_scenarios={
                            "sns": "https://docs.aws.amazon.com/code-library/latest/ug/cpp_1_sns_code_examples.html#scenarios",
                        }
                    )
                }
            },
        ),
        languages={"C++": language},
    )
    example_scenario = Example(
        file=Path("test_cpp.yaml"),
        id="sns_GoodScenario",
        title="Scenario title",
        title_abbrev="Scenario title abbrev",
        synopsis="scenario synopsis.",
        category="Scenarios",
        doc_filenames=DocFilenames(
            service_pages={
                "sns": "https://docs.aws.amazon.com/code-library/latest/ug/sns_example_sns_GoodScenario_section.html",
            },
            sdk_pages={
                "cpp": {
                    1: SDKVersion(
                        actions_scenarios={
                            "sns": "https://docs.aws.amazon.com/code-library/latest/ug/cpp_1_sns_code_examples.html#scenarios",
                        }
                    )
                }
            },
        ),
        services={
            "sns": {"GoodOne"},
        },
        languages={"C++": language},
    )
    assert parsed[0] == example_action
    assert parsed[1] == example_scenario


STRICT_TITLE_ERRORS = """
sns_BadOne:
   title: Disallowed title
   title_abbrev: Disallowed title abbrev
   synopsis: disallowed synopsis. 
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
     sns: {Different}
sns_BadScenario:
   category: Scenarios
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
     sns: {BadOne}
"""


def test_parse_strict_title_errors():
    meta = yaml.safe_load(STRICT_TITLE_ERRORS)
    _, errors = parse(
        Path("test_cpp.yaml"),
        meta,
        SDKS,
        SERVICES,
        set(),
        ValidationConfig(strict_titles=True),
    )
    expected = [
        metadata_errors.APICannotHaveTitleFields(
            file=Path("test_cpp.yaml"),
            id="sns_BadOne",
        ),
        metadata_errors.ActionNameFormat(
            file=Path("test_cpp.yaml"),
            id="sns_BadOne",
        ),
        metadata_errors.NonAPIMustHaveTitleFields(
            file=Path("test_cpp.yaml"),
            id="sns_BadScenario",
        ),
    ]
    assert expected == [*errors]


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
     ses:
"""


def test_parse_cross():
    meta = yaml.safe_load(CROSS_META)
    actual, errors = parse(
        Path("cross.yaml"),
        meta,
        SDKS,
        SERVICES,
        set(["cross_DeleteTopic_block.xml"]),
        DOC_GEN.validation,
    )
    assert len(errors) == 0
    assert len(actual) == 1
    language = Language(
        name="Java",
        property="java",
        versions=[Version(sdk_version=3, block_content="cross_DeleteTopic_block.xml")],
    )
    example = Example(
        file=Path("cross.yaml"),
        id="cross_DeleteTopic",
        category="Cross-service examples",
        title="Delete Topic",
        title_abbrev="delete topic",
        synopsis="",
        services={"ses": set(), "sns": set()},
        doc_filenames=DocFilenames(
            service_pages={
                "sns": "https://docs.aws.amazon.com/code-library/latest/ug/sns_example_cross_DeleteTopic_section.html",
                "ses": "https://docs.aws.amazon.com/code-library/latest/ug/ses_example_cross_DeleteTopic_section.html",
            },
            sdk_pages={
                "java": {
                    3: SDKVersion(
                        actions_scenarios={
                            "sns": "https://docs.aws.amazon.com/code-library/latest/ug/java_3_sns_code_examples.html#scenarios",
                            "ses": "https://docs.aws.amazon.com/code-library/latest/ug/java_3_ses_code_examples.html#scenarios",
                        }
                    )
                }
            },
        ),
        languages={"Java": language},
    )
    assert actual[0] == example


CURATED = """
s3_autogluon_tabular_with_sagemaker_pipelines:
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
    actual, errors = parse(
        Path("curated.yaml"),
        meta,
        SDKS,
        SERVICES,
        set(["block.xml"]),
        DOC_GEN.validation,
    )
    assert len(errors) == 0
    assert len(actual) == 1
    language = Language(
        name="Java",
        property="java",
        versions=[Version(sdk_version=2, block_content="block.xml")],
    )
    example = Example(
        id="s3_autogluon_tabular_with_sagemaker_pipelines",
        file=Path("curated.yaml"),
        category="Curated examples",
        title="AutoGluon Tabular with SageMaker Pipelines",
        title_abbrev="AutoGluon Tabular with SageMaker Pipelines",
        source_key="amazon-sagemaker-examples",
        languages={"Java": language},
        services={"s3": set()},
        doc_filenames=DocFilenames(
            service_pages={
                "s3": "https://docs.aws.amazon.com/code-library/latest/ug/s3_example_s3_autogluon_tabular_with_sagemaker_pipelines_section.html",
            },
            sdk_pages={
                "java": {
                    2: SDKVersion(
                        actions_scenarios={
                            "s3": "https://docs.aws.amazon.com/code-library/latest/ug/java_2_s3_code_examples.html#scenarios",
                        }
                    )
                }
            },
        ),
        synopsis="use AutoGluon with SageMaker Pipelines.",
    )

    assert actual[0] == example


def test_verify_load_successful():
    actual, errors = load(
        Path(__file__).parent / "test_resources/valid_metadata.yaml",
        DOC_GEN,
        set(["test block"]),
    )
    assert len(errors) == 0
    assert len(actual) == 1
    java = Language(
        name="Java",
        property="java",
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
        property="javascript",
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
                        genai="some",
                    )
                ],
                sdkguide=None,
                more_info=[],
            ),
        ],
    )

    php = Language(
        name="PHP",
        property="php",
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
        file=Path(__file__).parent / "test_resources/valid_metadata.yaml",
        id="sns_TestExample",
        title="Check whether a phone number is opted out using an &AWS; SDK",
        title_abbrev="Check whether a phone number is opted out",
        synopsis="check whether a phone number is opted out using some of the &AWS; SDKs that are available.",
        synopsis_list=["Check the one thing.", "Do some other thing."],
        guide_topic=Url(title="Test guide topic title", url="test-guide/url"),
        category="Usage",
        service_main=None,
        languages=languages,
        doc_filenames=DocFilenames(
            service_pages={
                "sqs": "https://docs.aws.amazon.com/code-library/latest/ug/sqs_example_sns_TestExample_section.html",
                "sns": "https://docs.aws.amazon.com/code-library/latest/ug/sns_example_sns_TestExample_section.html",
            },
            sdk_pages={
                "java": {
                    2: SDKVersion(
                        actions_scenarios={
                            "sqs": "https://docs.aws.amazon.com/code-library/latest/ug/java_2_sqs_code_examples.html#scenarios",
                            "sns": "https://docs.aws.amazon.com/code-library/latest/ug/java_2_sns_code_examples.html#scenarios",
                        }
                    )
                },
                "php": {
                    3: SDKVersion(
                        actions_scenarios={
                            "sqs": "https://docs.aws.amazon.com/code-library/latest/ug/php_3_sqs_code_examples.html#scenarios",
                            "sns": "https://docs.aws.amazon.com/code-library/latest/ug/php_3_sns_code_examples.html#scenarios",
                        }
                    )
                },
                "javascript": {
                    3: SDKVersion(
                        actions_scenarios={
                            "sqs": "https://docs.aws.amazon.com/code-library/latest/ug/javascript_3_sqs_code_examples.html#scenarios",
                            "sns": "https://docs.aws.amazon.com/code-library/latest/ug/javascript_3_sns_code_examples.html#scenarios",
                        }
                    )
                },
            },
        ),
        services={"sns": set(), "sqs": set()},
    )
    assert actual[0] == example


EMPTY_METADATA_PATH = Path(__file__).parent / "test_resources/empty_metadata.yaml"
ERRORS_METADATA_PATH = Path(__file__).parent / "test_resources/errors_metadata.yaml"
FORMATTER_METADATA_PATH = (
    Path(__file__).parent / "test_resources/formaterror_metadata.yaml"
)


@pytest.mark.parametrize(
    "filename,expected_errors",
    [
        (
            "empty_metadata.yaml",
            [
                metadata_errors.MissingField(
                    field="languages",
                    file=EMPTY_METADATA_PATH,
                    id="sns_EmptyExample",
                ),
                metadata_errors.ServiceNameFormat(
                    file=EMPTY_METADATA_PATH,
                    id="sns_EmptyExample",
                    svc="sns",
                    svcs=[],
                ),
            ],
        ),
        (
            "errors_metadata.yaml",
            [
                metadata_errors.APIMustHaveOneServiceOneAction(
                    file=ERRORS_METADATA_PATH,
                    id="sqs_WrongServiceSlug",
                    svc_actions="",
                ),
                metadata_errors.UnknownLanguage(
                    language="Perl",
                    file=ERRORS_METADATA_PATH,
                    id="sqs_WrongServiceSlug",
                ),
                metadata_errors.InvalidSdkGuideStart(
                    file=ERRORS_METADATA_PATH,
                    id="sqs_WrongServiceSlug",
                    language="Perl",
                    guide="https://docs.aws.amazon.com/absolute/link-to-my-guide",
                    sdk_version=1,
                ),
                metadata_errors.MissingBlockContentAndExcerpt(
                    file=ERRORS_METADATA_PATH,
                    id="sqs_WrongServiceSlug",
                    language="Perl",
                    sdk_version=1,
                ),
                metadata_errors.APIExampleCannotAddService(
                    file=ERRORS_METADATA_PATH,
                    id="sqs_WrongServiceSlug",
                    language="Perl",
                    sdk_version=1,
                ),
                metadata_errors.ServiceNameFormat(
                    file=ERRORS_METADATA_PATH,
                    id="sqs_WrongServiceSlug",
                    svc="sqs",
                    svcs=["sns"],
                ),
                metadata_errors.MissingField(
                    field="versions",
                    file=ERRORS_METADATA_PATH,
                    id="sqs_TestExample",
                    language="Java",
                ),
                metadata_errors.MissingBlockContentAndExcerpt(
                    file=ERRORS_METADATA_PATH,
                    id="sns_TestExample",
                    language="Java",
                    sdk_version=2,
                ),
                # example_errors.MissingSnippetTag(
                #     file="errors_metadata.yaml",
                #     id="sqs_TestExample",
                #     language="Java",
                #     sdk_version=2,
                #     tag="this.snippet.does.not.exist",
                # ),
                metadata_errors.UnknownService(
                    file=ERRORS_METADATA_PATH,
                    id="sns_TestExample2",
                    service="garbled",
                ),
                metadata_errors.InvalidGithubLink(
                    file=ERRORS_METADATA_PATH,
                    id="sns_TestExample2",
                    language="Java",
                    sdk_version=2,
                    link="github/link/to/README.md",
                ),
                metadata_errors.FieldError(
                    file=ERRORS_METADATA_PATH,
                    id="sns_TestExample2",
                    field="genai",
                    value="so much",
                    language="Java",
                    sdk_version=2,
                ),
                metadata_errors.BlockContentAndExcerptConflict(
                    file=ERRORS_METADATA_PATH,
                    id="cross_TestExample_Versions",
                    language="Java",
                    sdk_version=2,
                ),
                metadata_errors.MissingCrossContent(
                    file=ERRORS_METADATA_PATH,
                    id="cross_TestExample_Missing",
                    language="Java",
                    sdk_version=2,
                    block="missing_block_content.xml",
                ),
                metadata_errors.MissingBlockContentAndExcerpt(
                    file=ERRORS_METADATA_PATH,
                    id="snsBadFormat",
                    language="Java",
                    sdk_version=2,
                ),
                metadata_errors.NameFormat(
                    file=ERRORS_METADATA_PATH,
                    id="snsBadFormat",
                ),
            ],
        ),
        (
            "formaterror_metadata.yaml",
            [
                metadata_errors.NameFormat(
                    file=FORMATTER_METADATA_PATH,
                    id="WrongNameFormat",
                ),
                metadata_errors.UnknownService(
                    file=FORMATTER_METADATA_PATH,
                    id="cross_TestExample",
                    language="Java",
                    sdk_version=2,
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


TEST_SERVICES = {"test": {"Test", "Test2", "Test3", "1"}}


@pytest.mark.parametrize(
    "name,check_action,error_count",
    [
        ("serverless_Snippet", False, 0),
        ("test_Test", False, 0),
        ("test_Test", True, 0),
        ("test_Test_More", True, 1),
        ("test_NotThere", True, 1),
        ("cross_Cross", False, 0),
        ("other_Other", False, 1),
        ("test", False, 1),
    ],
)
def test_check_id_format(name, check_action, error_count):
    errors = MetadataErrors()
    check_id_format(name, TEST_SERVICES, check_action, errors)
    assert len(errors) == error_count


@pytest.mark.parametrize(
    ["a", "b", "d"],
    [
        (
            Example(
                id="ex_a",
                file=Path("file_a"),
                languages={
                    "a": Language(
                        name="a",
                        property="a",
                        versions=[
                            Version(
                                sdk_version=1,
                                excerpts=[Excerpt("a_v1", ["a1_snippet"])],
                            )
                        ],
                    )
                },
                services={"a_svc": {"ActionA"}},
            ),
            Example(
                id="ex_a",
                file=Path("file_b"),
                languages={
                    "a": Language(
                        name="a",
                        property="a",
                        versions=[
                            Version(
                                sdk_version=2,
                                excerpts=[Excerpt("a_v2", ["a2_snippet"])],
                            )
                        ],
                    ),
                    "b": Language(
                        name="b",
                        property="b",
                        versions=[
                            Version(
                                sdk_version=1,
                                excerpts=[Excerpt("b_v1", ["b1_snippet"])],
                            )
                        ],
                    ),
                },
                services={"b_svc": {"ActionB"}},
            ),
            Example(
                id="ex_a",
                file=Path("file_a"),
                languages={
                    "a": Language(
                        name="a",
                        property="a",
                        versions=[
                            Version(
                                sdk_version=1,
                                excerpts=[Excerpt("a_v1", ["a1_snippet"])],
                            ),
                            Version(
                                sdk_version=2,
                                excerpts=[Excerpt("a_v2", ["a2_snippet"])],
                            ),
                        ],
                    ),
                    "b": Language(
                        name="b",
                        property="b",
                        versions=[
                            Version(
                                sdk_version=1,
                                excerpts=[Excerpt("b_v1", ["b1_snippet"])],
                            )
                        ],
                    ),
                },
                services={"a_svc": {"ActionA"}, "b_svc": {"ActionB"}},
            ),
        )
    ],
)
def test_merge(a: Example, b: Example, d: Example):
    a.merge(b, MetadataErrors())
    assert a == d


@pytest.mark.parametrize(
    ["a", "b", "d"],
    [
        (
            Example(
                id="ex_a",
                file=Path("file_a"),
                languages={
                    "a": Language(
                        name="a",
                        property="a",
                        versions=[
                            Version(
                                sdk_version=1,
                                excerpts=[Excerpt("a_v1", ["a1_snippet"])],
                            )
                        ],
                    )
                },
            ),
            Example(
                id="ex_a",
                file=Path("file_b"),
                languages={
                    "a": Language(
                        name="a",
                        property="a",
                        versions=[
                            Version(
                                sdk_version=1,
                                excerpts=[Excerpt("a2_v1", ["a2_snippet"])],
                            )
                        ],
                    )
                },
            ),
            Example(
                id="ex_a",
                file=Path("file_a"),
                languages={
                    "a": Language(
                        name="a",
                        property="a",
                        versions=[
                            Version(
                                sdk_version=1,
                                excerpts=[Excerpt("a_v1", ["a1_snippet"])],
                            )
                        ],
                    ),
                },
            ),
        )
    ],
)
def test_merge_conflict(a: Example, b: Example, d: Example):
    errors = MetadataErrors()
    a.merge(b, errors)
    assert a == d
    assert errors[0] == ExampleMergeConflict(
        id=a.id, file=a.file, language="a", sdk_version=1, other_file=Path("file_b")
    )


def test_no_duplicate_title_abbrev():
    errors = MetadataErrors()
    doc_gen = DocGen(
        Path(__file__).parent / "test_no_duplicate_title_abbrev",
        errors=errors,
        examples={
            "a": Example(
                id="a",
                file=Path("a"),
                title_abbrev="abbr",
                category="cat",
                languages={
                    "java": Language(
                        name="java", property="java", versions=[Version(sdk_version=1)]
                    )
                },
                services={"svc": set()},
            ),
            "b": Example(
                id="b",
                file=Path("b"),
                title_abbrev="abbr",
                category="cat",
                languages={
                    "java": Language(
                        name="java", property="java", versions=[Version(sdk_version=1)]
                    )
                },
                services={"svc": set(), "cvs": set()},
            ),
        },
    )
    doc_gen.validate()

    expected = [
        metadata_errors.DuplicateTitleAbbrev(
            id="a, b", title_abbrev="abbr", language="svc:cat"
        )
    ]

    assert expected == [*errors]


if __name__ == "__main__":
    pytest.main([__file__, "-vv"])
