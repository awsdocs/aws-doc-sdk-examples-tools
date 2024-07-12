## AWS Doc SDK Examples Tools

This python library is a set of tools to manage [AWS Doc SDK Example metadata](https://github.com/awsdocs/aws-doc-sdk-examples/tree/main/.doc_gen).
It is used by the AWS Doc SDK Examples team, as well as tributary sources of
example snippets.

-tools:

- Validates example metadata.
- Provides an API to program against example metadata.
- Hydrates additional derived data not explicitly written by engineers into example metadata.

## Check-in tests

### Purpose

The check-in tests are run whenever a pull request is submitted or changed. They
can be included in a Github Action with a job like this:

```
jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - name: checkout repo content
        uses: actions/checkout@v4
      - name: validate metadata
        uses: awsdocs/aws-doc-sdk-examples-tools@main
```

The check-in tests walk the full repository and scan code files to look for
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

### Updating validations

The above configuration tracks the `main` branch directly. To follow more stable releases, use the most recent release tag in the github action.

```
uses: awsdocs/aws-doc-sdk-examples-tools@v2024-07-11-A
```

### Running during development

```
python3.8 -m venv .venv
# With a python 3.8 venv in .venv
source .venv/bin/activate # Adjust for windows as necessary
python -m pip install -r requirements.txt
python -m pip install -e .
python -m mypy aws_doc_sdk_examples_tools
python -m pytest -vv
python -m black --check
```

## Validation Extensions

Some validation options can be extended by creating `.doc_gen/validation.yaml`.

- `allow_list`: The 40-character check is _very_ sensitive. To allow certain patterns, add them as a string to the `allow_list` key, which will be loaded as a set of strings to allow.
- `sample_files`: Sample files are only allowed with certain names. To allow additional sample files, add their file name (with extension, but not path) to this list.

## New Releases

1. When making a release, find the most recent commit sha (or sha that will be tagged for the release).
2. Update https://github.com/awsdocs/aws-doc-sdk-examples/blob/main/.github/workflows/validate-doc-metadata.yml to that tag.
  * Also add that commit sha to the [validation config](https://github.com/awsdocs/aws-doc-sdk-examples/blob/main/.doc_gen/validation.yaml)
3. Create a PR in aws-doc-sdk-examples (do not submit it) to run tests.
4. When tests in the main repo are passing, create a tag in this -tools repo at that sha with the format `YYYY-MM-DD-A`, where `YYYY-MM-DD` are the year, month, and day of the release and -A is -A, -B, -C etc for multiple releases within a day.
5. Push that tag.
6. Update the PR from 2 with that tag, remove the validation sha exception, and push that for draft.
7. Create a release using the automated "Create release from tag" button.
8. Perform internal update process.

## Security

See [CONTRIBUTING](CONTRIBUTING.md#security-issue-notifications) for more information.

## License

This project is licensed under the Apache-2.0 License.
