import json
import tempfile
import pytest
from pathlib import Path

from aws_doc_sdk_examples_tools.lliam.service_layer.run_ailly import (
    process_ailly_files,
    VALUE_PREFIXES,
)


@pytest.fixture
def test_environment():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        ailly_dir = temp_path / "ailly_dir"
        ailly_dir.mkdir(exist_ok=True)

        output_path = temp_path / "iam_updates.json"

        create_sample_ailly_files(ailly_dir)

        yield {
            "ailly_dir": ailly_dir,
            "output_path": output_path,
            "temp_dir": temp_path,
        }


def create_sample_ailly_files(ailly_dir):
    # Sample file 1
    file1_path = ailly_dir / "iam-policies.SomeGuide.1.md.ailly.md"
    with open(file1_path, "w") as f:
        f.write(
            """# IAM Policy Example for S3 Bucket Access

This example demonstrates how to create an IAM policy that grants read-only access to an S3 bucket.

## Policy Details

===
title => Grant Read-Only Access to an S3 Bucket
title_abbrev => S3 Read-Only
synopsis => This example shows how to create an IAM policy that grants read-only access to objects in an S3 bucket.
description => This policy grants permissions to list and get objects from a specific S3 bucket. It's useful for scenarios where users need to view but not modify bucket contents.
service => IAM
category => Security
languages => JSON, AWS CLI
===

## Implementation

Here's how you would implement this policy:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "s3:GetObject",
        "s3:ListBucket"
      ],
      "Resource": [
        "arn:aws:s3:::example-bucket",
        "arn:aws:s3:::example-bucket/*"
      ]
    }
  ]
}
```

## Additional Notes

Remember to replace 'example-bucket' with your actual bucket name when using this policy.
"""
        )

    # Sample file 2
    file2_path = ailly_dir / "iam-policies.SomeGuide.2.md.ailly.md"
    with open(file2_path, "w") as f:
        f.write(
            """# IAM Policy Example for EC2 Instance Management

This example demonstrates how to create an IAM policy for EC2 instance management.

## Policy Details

===
title => Manage EC2 Instances in a Specific Region
title_abbrev => Region Specific EC2
synopsis => This example shows how to create an IAM policy that allows management of EC2 instances in a specific AWS region.
description => This policy grants permissions to view, start, stop, and reboot EC2 instances in a specific region. It's useful for operations teams who need to manage instance lifecycles.
service => IAM
category => Security
languages => JSON, AWS CLI
===

## Implementation

Here's how you would implement this policy:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "ec2:DescribeInstances",
        "ec2:StartInstances",
        "ec2:StopInstances",
        "ec2:RebootInstances"
      ],
      "Resource": "*",
      "Condition": {
        "StringEquals": {
          "aws:RequestedRegion": "us-west-2"
        }
      }
    }
  ]
}
```

## Additional Notes

Modify the region condition to match your specific requirements.
"""
        )


def test_process_ailly_files(test_environment):
    ailly_dir = test_environment["ailly_dir"]
    output_path = test_environment["output_path"]

    process_ailly_files(ailly_dir, output_path)

    assert output_path.exists()

    with open(output_path, "r") as f:
        results = json.load(f)

    assert len(results) == 1
    assert len(list(results.values())[0]) == 2

    for example in results.get("SomeGuide"):
        assert example["title"].startswith(f"{VALUE_PREFIXES.get('title')}")
