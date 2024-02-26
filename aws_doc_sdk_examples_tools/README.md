# Scripts

The scripts contained in this module are primarily for use by the AWS
Code Examples team. These ensure .doc_gen/metadata is appropriately formatted,
and a project to be included in AWS docs meets certain validation rules.

### Prerequisites

To run this script, you must have the following installed globally or in a virtual
environment:

- Python 3.8 or later
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
