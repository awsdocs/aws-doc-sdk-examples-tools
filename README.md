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

1. **Create a testing branch** from [aws-doc-sdk-examples:main](https://github.com/awsdocs/aws-doc-sdk-examples).

1. **Find the most recent commit SHA in [aws-doc-sdk-examples-tools:main](https://github.com/awsdocs/aws-doc-sdk-examples-tools/commits/main/)**.

1. **Update your testing branch**: Add your SHA to the following files in tag format (e.g. `awsdocs/aws-doc-sdk-examples-tools@e7c283e916e8efc9113277e2f38c8fa855a79d0a`):

  * [.github/workflows/validate-doc-metadata.yml](https://github.com/awsdocs/aws-doc-sdk-examples/blob/main/.github/workflows/validate-doc-metadata.yml)
  * [.doc_gen/validation.yaml](https://github.com/awsdocs/aws-doc-sdk-examples/blob/main/.doc_gen/validation.yaml)

1. **Create a PR from branch**
Create a Pull Request (PR) in the aws-doc-sdk-examples repository, but do not submit it yet. This PR will be used to run tests.

1. **Wait for tests to pass** before continuing to next section.

### 2. Deployment

1. **Create a tag in the -tools repo**: Once the tests pass, create a tag in the -tools repository at the same SHA you identified earlier. The tag format should be YYYY-MM-DD-A, where YYYY-MM-DD represents the year, month, and day of the release, and -A is used for the first release of the day. Use -B, -C, etc., for subsequent releases on the same day.

1. **Push the tag: Push the tag you created in step 6 to the -tools repository.

1. **Update the PR with the new tag: In the PR you created in step 4, update the commit SHA with the new tag you pushed in step 7. Remove the validation SHA exception, and push the changes for draft review.

1. **Create a release: Use the automated "Create release from tag" button to create a new release based on the tag you pushed in step 7.

1. **Perform internal update process: Perform any internal update processes required for the release.

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
