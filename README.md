## AWS Doc SDK Examples Tools

This python library is a set of tools to manage [AWS Doc SDK Example metadata](https://github.com/awsdocs/aws-doc-sdk-examples/tree/main/.doc_gen).
It is used by the AWS Doc SDK Examples team, as well as tributary sources of
example snippets.

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

## Validation Extensions

Some validation options can be extended by creating `.doc_gen/validation.yaml`.

- `allow_list`: The 40-character check is _very_ sensitive. To allow certain patterns, add them as a string to the `allow_list` key, which will be loaded as a set of strings to allow.
- `sample_files`: Sample files are only allowed with certain names. To allow additional sample files, add their file name (with extension, but not path) to this list.

## Security

See [CONTRIBUTING](CONTRIBUTING.md#security-issue-notifications) for more information.

## License

This project is licensed under the Apache-2.0 License.
