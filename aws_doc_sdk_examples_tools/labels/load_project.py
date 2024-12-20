import argparse
from ast import literal_eval
from pathlib import Path
from time import time


from aws_doc_sdk_examples_tools.doc_gen import DocGen
from .from_doc_gen import from_doc_gen
from .labels import select


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--root",
        default=f"{Path(__file__).parent.parent.parent}",
        help="The root path from which to search for files to check. The default is the root of the git repo (two up from this file).",
    )
    parser.add_argument(
        "--doc_gen_only",
        type=literal_eval,
        default=True,
        help="Only perform extended validation on snippet contents",
        required=False,
    )
    parser.add_argument(
        "--strict_titles",
        type=literal_eval,
        default=False,
        help="Strict title requirements: Action examples must not have title/title_abbrev; non-Action examples "
        "must have them.",
        required=False,
    )
    args = parser.parse_args()
    root_path = Path(args.root).resolve()

    doc_gen = DocGen.from_root(root=root_path)
    doc_gen.collect_snippets()

    labeled = from_doc_gen(doc_gen)

    # print(labeled)
    print('Services: ', len(labeled['services']))
    print('SDKs: ', len(labeled['sdks']))
    print('Examples: ', len(labeled['examples']))
    print('Snippets: ', len(labeled['snippets']))

    for sdk in labeled['sdks']:
        before = time()
        snippets = select(labeled['snippets'], sdk)
        after = time()
        elapsed = after - before
        print(f"{sdk.language}:{sdk.version} has {len(snippets)} snippets (took {(elapsed * 1000):.2} ms)")


if __name__ == "__main__":
    exit(main())
