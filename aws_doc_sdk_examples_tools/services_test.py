# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

from pathlib import Path
from typing import Dict, Tuple
import pytest
import yaml

from aws_doc_sdk_examples_tools import metadata_errors
from .services import (
    parse,
    Service,
    ServiceGuide,
    ServiceExpanded,
)


def load(path: str) -> Tuple[Dict[str, Service], metadata_errors.MetadataErrors]:
    root = Path(__file__).parent
    filename = root / "test_resources" / path
    with open(filename) as file:
        meta = yaml.safe_load(file)
    return parse(filename, meta)


def test_empty_services():
    _, errs = load("empty_services.yaml")
    assert [*errs] == [
        metadata_errors.MissingServiceBody(
            file=Path(__file__).parent / "test_resources/empty_services.yaml",
            id="sns",
        )
    ]


def test_services_entity_usage():
    _, errs = load("entityusage_services.yaml")
    assert [*errs] == [
        metadata_errors.MappingMustBeEntity(
            file=Path(__file__).parent / "test_resources/entityusage_services.yaml",
            id="sns",
            field="long",
            value="SNSlong",
        ),
        metadata_errors.MappingMustBeEntity(
            file=Path(__file__).parent / "test_resources/entityusage_services.yaml",
            id="sns",
            field="short",
            value="SNS",
        ),
        metadata_errors.MissingField(
            file=Path(__file__).parent / "test_resources/entityusage_services.yaml",
            id="sns",
            field="version",
        ),
        metadata_errors.MissingField(
            file=Path(__file__).parent / "test_resources/entityusage_services.yaml",
            id="sns",
            field="api_ref",
        ),
    ]


def test_services():
    examples, _ = load("services.yaml")
    assert examples == {
        "s3": Service(
            short="&S3;",
            expanded=ServiceExpanded(
                long="Amazon Simple Storage Service (Amazon S3)", short="Amazon S3"
            ),
            long="&S3long;",
            sort="S3",
            version="s3-2006-03-01",
            caveat="The examples in this section are pretty neat, and we recommend you print them out so you can read them in bed with a good glass of wine.",
            api_ref="AmazonS3/latest/API/Welcome.html",
            blurb="is storage for the internet. You can use Amazon S3 to store and retrieve any amount of data at any time, from anywhere on the web.",
            guide=ServiceGuide(
                subtitle="User Guide",
                url="AmazonS3/latest/userguide/Welcome.html",
            ),
        ),
        "sns": Service(
            short="&SNS;",
            long="&SNSlong;",
            expanded=ServiceExpanded(
                long="Amazon Simple Notification Service (Amazon SNS)",
                short="Amazon SNS",
            ),
            sort="SNS",
            version="sns-2010-03-31",
            bundle="sqs",
        ),
        "sqs": Service(
            short="&SQS;",
            long="&SQSlong;",
            expanded=ServiceExpanded(
                long="Amazon Simple Queue Service (Amazon SQS)", short="Amazon SQS"
            ),
            sort="SQS",
            tags={
                "product_categories": set(["Category 1", "Category 2"]),
            },
            version="sqs-2012-11-05",
            bundle="sqs",
        ),
        "textract": Service(
            short="&TEXTRACT;",
            long="&TEXTRACTlong;",
            expanded=ServiceExpanded(long="Amazon Textract", short="Amazon Textract"),
            sort="Textract",
            tags={"product_categories": set(["Category 1"])},
            version="textract-2018-06-27",
        ),
    }


if __name__ == "__main__":
    pytest.main([__file__, "-vv"])
