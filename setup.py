# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

from setuptools import setup

setup(
    name="aws_doc_sdk_examples_tools",
    version="2024.43.0",
    packages=["aws_doc_sdk_examples_tools"],
    package_data={"aws_doc_sdk_examples_tools": ["config/*.yaml"]},
    entry_points={
        "console_scripts": ["doc-gen=aws_doc_sdk_examples_tools.doc_gen_cli:main"],
    },
    build_requires=[
        "setuptools>=40.8.0",
        "wheel",
    ],
    install_requires=[
        "pathspec==0.11.2",
        "PyYAML==6.0.1",
        "yamale==4.0.4",
    ],
)
