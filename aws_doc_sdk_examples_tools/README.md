# Scripts

The scripts contained in this module are primarily for use by the AWS
Code Examples team. These ensure .doc_gen/metadata is appropriately formatted,
and a project to be included in AWS docs meets certain validation rules.

## Checkin tests

### Purpose

The checkin tests are run whenever a pull request is submitted or changed. They
can be included in a Github Action with a job like this:

```
jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - name: checkout repo content
        uses: actions/checkout@v3
      - name: validate metadata
        uses: awsdocs/aws-doc-sdk-examples-tools@main
```

The checkin tests walk the full repository and scan code files to look for
the following issues.

- Disallow a list of specified words.
- Disallow any 20- or 40- character strings that fit a specified regex profile
  that indicates they might be secret access keys. Allow strings that fit the
  regex profile if they are in the allow list.
- Disallow file names that contain 20- or 40- character strings that fit the same
  regex profile, unless the filename is in the allow list.
- Verify that snippet-start and snippet-end tags are in matched pairs. You are
  not required to include these tags, but if you do they must be in pairs.
- Ensures any snippet_file in metadata excerpts are present in the repo.

A count of errors found is returned. When CI receives a non-zero return code,
it treats the checks as failed and displays a message in the pull request.

### Prerequisites

To run this script, you must have the following installed globally or in a virtual
environment:

- Python 3.9 or later
- PyTest 5.3.5 or later (to run unit tests)

### Running the script

The typical usage of this script is to check for certain disallowed strings and
verify matched snippet tags when submitting a pull request. You can run the script
manually by running the following in the root folder of your GitHub clone.

```
python aws_doc_sdk_examples_tools/validate.py --root ${PATH_TO_PROJECT}
```

The script can also be used to verify individual folders. If you want to verify
just the files in a specific folder and its subfolders, use the `--root` option.
For example, to scan just the `file_transfer` folder in the Python S3 example section,
run the following command.

### Running the tests

To run the unit tests associated with this script, in a command window at the
`aws_doc_sdk_examples_tools` folder of the repository, run `python -m pytest`.

---

Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
SPDX-License-Identifier: Apache-2.0
