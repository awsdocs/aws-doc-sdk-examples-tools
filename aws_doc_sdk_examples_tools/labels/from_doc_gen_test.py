from pathlib import Path

from aws_doc_sdk_examples_tools.doc_gen import DocGen
from aws_doc_sdk_examples_tools.metadata_errors import MetadataErrors
from aws_doc_sdk_examples_tools.snippets import Snippet as DocGenSnippet

from . import from_doc_gen
from . import known_labels
from .labels import Sdk, Service, Example, Snippet, Expanded, Label, Excerpt, Context


def test_from_doc_gen():
    errors = MetadataErrors()
    base = Path(__file__).parent.parent / "test_resources"
    doc_gen = DocGen(base, errors).for_root(base, base)
    doc_gen.process_metadata(doc_gen.root / "valid_metadata.yaml")
    doc_gen.collect_snippets()
    doc_gen.snippets = {
        "medical-imaging.JavaScript.datastore.createDatastoreV3": DocGenSnippet(
            id="medical-imaging.JavaScript.datastore.createDatastoreV3",
            file="javascript/medical_imaging/create_datastore.js",
            line_end=13,
            line_start=10,
            code='client.send({\nname: "test"}\n)',
        ),
        "php.snippet.tag.1": DocGenSnippet(
            id="php.snippet.tag.1",
            file="php/medical_imaging/create_datastore.php",
            line_start=10,
            line_end=13,
            code="tag 1 a\ntag 1 b\ntag 1 c",
        ),
        "php.snippet.tag.2": DocGenSnippet(
            id="php.snippet.tag.2",
            file="php/medical_imaging/create_datastore.php",
            line_start=20,
            line_end=23,
            code="tag 2 a\ntag 2 b\ntag 2 c",
        ),
        "snippet_file.txt": DocGenSnippet(
            id="snippet_file.txt",
            file="php/medical_imaging/helper.php",
            line_start=0,
            line_end=2,
            code="helper a\nhelper b",
        ),
    }

    as_labels = from_doc_gen(doc_gen)

    assert as_labels["sdks"] == frozenset(
        [
            Sdk(
                version="1",
                language="cpp",
                name=Expanded(long="&CPPlong;", short="&CPP;"),
                labels=[Label(name="bookmark", value="code-examples")],
                guide="&guide-cpp-dev;",
            ),
            Sdk(
                version="1",
                language="go",
                name=Expanded(long="&Golong; V1", short="&Go; V1"),
                guide="&guide-go-dev;",
            ),
            Sdk(
                version="2",
                language="go",
                name=Expanded(
                    long="&Golong; V2",
                    short="&Go; V2",
                ),
                guide="&guide-go-dev;",
            ),
            Sdk(
                version="1",
                language="java",
                name=Expanded(long="&Javalong;", short="&Java;"),
                guide="&guide-javav2-dev;",
            ),
            Sdk(
                version="2",
                language="java",
                name=Expanded(long="&JavaV2long;", short="&Java;"),
                guide="&guide-javav2-dev;",
            ),
            Sdk(
                version="2",
                language="javascript",
                name=Expanded(long="&JSBlong; V2", short="&JSB; V2"),
                guide="&guide-jsb-dev;",
            ),
            Sdk(
                version="3",
                language="javascript",
                name=Expanded(long="&JSBlong; V3", short="&JSB; V3"),
                #   api_ref:
                #     uid: "AWSJavaScriptSDK",
                #     name: "&guide-jsb-api;",
                #     link_template: "AWSJavaScriptSDK/v3/latest/clients/client-{{.Service}}/classes/{{.OperationLower}}command.html",
                guide="&guide-jsb-dev;",
            ),
            Sdk(
                version="1",
                language="kotlin",
                name=Expanded(
                    long="&AWS; SDK for Kotlin", short="&AWS; SDK for Kotlin"
                ),
                labels=[
                    Label(
                        name="caveat",
                        value="This is prerelease documentation for a feature in preview release. It is subject to change.",
                    )
                ],
                guide="&NO_GUIDE;",
            ),
            Sdk(
                version="3",
                language="csharp",
                name=Expanded(long="&NETlong;", short="&NET;"),
                #   title_override:
                #     title: "Additional &NET; code examples",
                #     title_abbrev: "Additional code examples",
                guide="&guide-net-dev;",
            ),
            Sdk(
                version="3",
                language="php",
                name=Expanded(long="&PHPlong;", short="&PHP;"),
                guide="&guide-php-dev;",
            ),
            Sdk(
                version="3",
                language="python",
                name=Expanded(long="&Python3long;", short="&Python3;"),
                guide="&guide-python3-gsg;",
            ),
            Sdk(
                version="3",
                language="ruby",
                name=Expanded(long="&Rubylong;", short="&Ruby;"),
                guide="&guide-ruby-dev;",
            ),
        ]
    )

    assert as_labels["services"] == frozenset(
        [
            Service(
                id="s3",
                name=Expanded(short="&S3;", long="&S3long;"),
                expanded=Expanded(
                    short="Amazon S3",
                    long="Amazon Simple Storage Service (Amazon S3)",
                ),
                sort="S3",
                version="s3-2006-03-01",
                labels=[
                    Label(
                        name=known_labels.CAVEAT,
                        value="The examples in this section are pretty neat, and we recommend you print them out so you can read them in bed with a good glass of wine.",
                    ),
                    Label(
                        name=known_labels.BLURB,
                        value="is storage for the internet. You can use Amazon S3 to store and retrieve any amount of data at any time, from anywhere on the web.",
                    ),
                ],
                api_ref="AmazonS3/latest/API/Welcome.html",
                #   guide:
                #     subtitle: User Guide
                #     url: AmazonS3/latest/userguide/Welcome.html
            ),
            Service(
                id="medical-imaging",
                name=Expanded(short="&AHI;", long="&AHIlong;"),
                expanded=Expanded(short="HealthImaging", long="HealthImaging"),
                sort="HealthImaging",
                version="medical-imaging-2023-07-19",
            ),
            Service(
                id="sqs",
                name=Expanded(short="&SQS;", long="&SQSlong;"),
                expanded=Expanded(short="Amazon SQS", long="Amazon SQS"),
                sort="SQS",
                labels=[
                    Label(name=known_labels.CATEGORY, value="Category 1"),
                    Label(name=known_labels.CATEGORY, value="Category 2"),
                    Label(name=known_labels.BUNDLE, value="sqs"),
                ],
                version="sqs-2012-11-05",
            ),
            Service(
                id="textract",
                name=Expanded(short="&TEXTRACT;", long="&TEXTRACTlong;"),
                expanded=Expanded(short="Amazon Textract", long="Amazon Textract"),
                sort="Textract",
                labels=[
                    Label(name=known_labels.CATEGORY, value="Category 1"),
                ],
                version="textract-2018-06-27",
            ),
        ]
    )

    assert as_labels["examples"] == frozenset(
        [
            Example(
                id="medical-imaging_TestExample",
                title="Check whether a phone number is opted out using an &AWS; SDK",
                title_abbrev="Check whether a phone number is opted out",
                synopsis="check whether a phone number is opted out using some of the &AWS; SDKs that are available.",
                synopsis_list=[
                    "Check the one thing.",
                    "Do some other thing.",
                ],
                # guide_topic:
                #     title: Test guide topic title
                #     url: test-guide/url
                labels=[
                    Label(name=known_labels.CATEGORY, value="Usage"),
                    Label(name=known_labels.SERVICE, value="medical-imaging"),
                ],
            )
        ]
    )

    assert as_labels["snippets"] == frozenset(
        [
            Snippet(
                id="medical-imaging_TestExample:java:2",
                excerpts=[Excerpt(description="test block")],
                labels=[
                    Label(name=known_labels.SDK, value="java:2"),
                    Label(name=known_labels.ACTION, value="create_datastore"),
                    Label(name=known_labels.SERVICE, value="medical-imaging"),
                ],
            ),
            Snippet(
                id="medical-imaging_TestExample:javascript:3",
                excerpts=[
                    Excerpt(description="Descriptive"),
                    Excerpt(
                        path="javascript/medical_imaging/create_datastore.js",
                        range=(10, 13),
                        content='client.send({\nname: "test"}\n)',
                    ),
                ],
                labels=[
                    Label(name=known_labels.SDK, value="javascript:3"),
                    Label(name=known_labels.ACTION, value="create_datastore"),
                    Label(name=known_labels.SERVICE, value="medical-imaging"),
                    Label(name=known_labels.SERVICE, value="s3"),
                ],
            ),
            Snippet(
                id="medical-imaging_TestExample:php:3",
                context=Context(),
                excerpts=[
                    Excerpt(description="Optional description."),
                    Excerpt(
                        path="php/medical_imaging/create_datastore.php",
                        range=(10, 13),
                        content="tag 1 a\ntag 1 b\ntag 1 c",
                    ),
                    Excerpt(
                        path="php/medical_imaging/create_datastore.php",
                        range=(20, 23),
                        content="tag 2 a\ntag 2 b\ntag 2 c",
                    ),
                    Excerpt(
                        path="php/medical_imaging/helper.php",
                        range=(0, 2),
                        content="helper a\nhelper b",
                    ),
                ],
                labels=[
                    Label(name=known_labels.SDK, value="php:3"),
                    Label(name=known_labels.ACTION, value="create_datastore"),
                    Label(name=known_labels.SERVICE, value="medical-imaging"),
                ],
            ),
        ]
    )
