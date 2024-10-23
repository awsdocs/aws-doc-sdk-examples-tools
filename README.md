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
uses: awsdocs/aws-doc-sdk-examples-tools@2024-08-26-A
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

There are two stages, testing and deployment.

### 1. Testing

1. **Create a testing branch** from [aws-doc-sdk-examples@main](https://github.com/awsdocs/aws-doc-sdk-examples/tree/main).
2. **Find the most recent commit SHA in [aws-doc-sdk-examples-tools/commits/main](https://github.com/awsdocs/aws-doc-sdk-examples-tools/commits/main/)**.
3. **Update your testing branch**: With your commit SHA (format: `org/repo@hash`, e.g. `awsdocs/aws-doc-sdk-examples-tools@e7c283e916e8efc9113277e2f38c8fa855a79d0a`), update the following files:
   - In [.github/workflows/validate-doc-metadata.yml](https://github.com/awsdocs/aws-doc-sdk-examples/blob/main/.github/workflows/validate-doc-metadata.yml), replace the current tag with the SHA.
   - Add only the commit SHA to the `allow_list` field in [.doc_gen/validation.yaml](https://github.com/awsdocs/aws-doc-sdk-examples/blob/main/.doc_gen/validation.yaml).
4. **Open a Draft PR to main branch**: Do not publish for review. Wait for checks/tests to pass on the PR.

### 2. Deployment

1. **Update the -tools version**: Once the tests pass, run `stamp.sh --release`. This will:
    - update `setup.py`
    - create a tag
    - push the tag to `main`.
1. **Update your testing PR branch**: Remove SHA and add tag to [validate-doc-metadata.yml](https://github.com/awsdocs/aws-doc-sdk-examples/blob/main/.github/workflows/validate-doc-metadata.yml)
   - NOTE: Remove the SHA from [.doc_gen/validation.yaml](https://github.com/awsdocs/aws-doc-sdk-examples/blob/main/.doc_gen/validation.yaml)
   - This is easily accomplished in the Github UI.
1. **Create a release**: Use the automated ["Create release from tag" button](https://github.com/awsdocs/aws-doc-sdk-examples-tools/releases/new) to create a new release with the new tag.
1. **Perform internal update process**.
   - See `update.sh` script in internal package.

## Security

See [CONTRIBUTING](CONTRIBUTING.md#security-issue-notifications) for more information.

## License

This project is licensed under the Apache-2.0 License.
