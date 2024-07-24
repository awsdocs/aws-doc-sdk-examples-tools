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
There are 2 stages: testing and deployment.

### 1. Testing

1. **Create a testing branch** from [aws-doc-sdk-examples@main](https://github.com/awsdocs/aws-doc-sdk-examples/tree/main).

1. **Find the most recent commit SHA in [aws-doc-sdk-examples-tools:main](https://github.com/awsdocs/aws-doc-sdk-examples-tools/commits/main/)**.

1. **Update your testing branch**: Add your SHA as a tag (`org/repo@tag`, e.g. `awsdocs/aws-doc-sdk-examples-tools@e7c283e916e8efc9113277e2f38c8fa855a79d0a`) to the following files:

  * [.github/workflows/validate-doc-metadata.yml](https://github.com/awsdocs/aws-doc-sdk-examples/blob/main/.github/workflows/validate-doc-metadata.yml)
  * [.doc_gen/validation.yaml](https://github.com/awsdocs/aws-doc-sdk-examples/blob/main/.doc_gen/validation.yaml)

1. **Open a Draft PR to main branch**: Do not publish for review. Wait for checks/tests to pass on the PR.

### 2. Deployment

1. **Create a -tools tag**: Once the tests pass, create a tag in the -tools repository at the same SHA you identified earlier.
   - NOTE: tag format is `YYYY-MM-DD-A`, where `YYYY-MM-DD` represents release date, and `-A` is used for the first release of the day (followed by `-B`, `-C`, etc., for subsequent same-day releases)

Here is a command line example, tested on Mac:
```
TAG_NAME=$(date +%Y-%m-%d)-A && \
  SHA=$(git rev-parse HEAD) && \
  git tag -a "$TAG_NAME" "$SHA" -m "Release $TAG_NAME" && \
  git push origin "$TAG_NAME"
```

1. **Update your testing PR branch**: Remove SHA and add tag to [validate-doc-metadata.yml](https://github.com/awsdocs/aws-doc-sdk-examples/blob/main/.github/workflows/validate-doc-metadata.yml)
  * NOTE: Remove the SHA from [.doc_gen/validation.yaml](https://github.com/awsdocs/aws-doc-sdk-examples/blob/main/.doc_gen/validation.yaml)
  * This is easily accomplished in the UI.

1. **Create a release**: Use the automated ["Create release from tag" button](https://github.com/awsdocs/aws-doc-sdk-examples-tools/releases/new) to create a new release with the new tag.

1. **Perform internal update process**.
   
## Security

See [CONTRIBUTING](CONTRIBUTING.md#security-issue-notifications) for more information.

## License

This project is licensed under the Apache-2.0 License.
