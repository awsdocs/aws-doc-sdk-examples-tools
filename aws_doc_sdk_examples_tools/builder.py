from dataclasses import dataclass, field
import logging
from pathlib import Path
import re
from typing import List, Optional, cast

from aws_doc_sdk_examples_tools.doc_gen import DocGen
from aws_doc_sdk_examples_tools.fs import Fs, PathFs
from aws_doc_sdk_examples_tools.snippets import write_snippets

logging.basicConfig(level=logging.INFO)

logger = logging.getLogger(Path(__file__).name)


IAM_PATTERN = re.compile(r'"Version"\s*:\s*"20(08|12)-10-17"\s*,')
IAM_PATTERN_SLASHES = re.compile(r'\\"Version\\"\s*:\s*\\"20(08|12)-10-17\\"\s*,')
# This exciting set of unicode characters is the expanded version of the &IAM-2025-waiver; entity.
IAM_WAIVER = '"Version":"2012-10-17",\u0009\u0009\u0020\u0009\u0020\u0009\u0020'
IAM_WAIVER_SLASHES = '\\"Version\\":\\"2012-10-17\\",\u0009\u0009\u0020\u0009\u0020\u0009\u0020'


def _iam_replace_all(source: Optional[str]):
    if source:
        return IAM_PATTERN_SLASHES.subn(IAM_WAIVER_SLASHES, IAM_PATTERN.subn(IAM_WAIVER, source)[0])[0]
    return None


def _iam_fixup_metadata(meta_folder: Path):
    for meta_path in meta_folder.glob("**/*_metadata.yaml"):
        with meta_path.open("r") as meta_file:
            contents = meta_file.read()
        contents = cast(str, _iam_replace_all(contents))
        with meta_path.open("w") as meta_file:
            meta_file.write(contents)


def _iam_fixup_docgen(doc_gen: DocGen) -> DocGen:
    # For performance, do this mutably, but keep the signature open to making DocGen frozen
    for snippet in doc_gen.snippets.values():
        snippet.code = cast(str, _iam_replace_all(snippet.code))
    return doc_gen


@dataclass
class Builder:
    root: Path
    dest: Path
    doc_gen_folder = ".doc_gen"
    snippet_files_folder = "snippet_files"
    fs: Fs = field(default_factory=PathFs)
    _doc_gen: DocGen = field(init=False)

    def __post_init__(self):
        self._doc_gen = DocGen.from_root(self.root)

    def copy_doc_gen(self):
        tmp_mirror_doc_gen = self.root / self.doc_gen_folder
        mirror_doc_gen = self.dest / self.doc_gen_folder
        logger.info(f"Moving cloned files into package from {tmp_mirror_doc_gen} to {mirror_doc_gen}")
        try:
            self.fs.copytree(tmp_mirror_doc_gen, mirror_doc_gen)
        except Exception as e:
            logger.error(f"Failed copy directory {tmp_mirror_doc_gen} to {mirror_doc_gen}\n{e}")
            logger.error(e)
            raise

    def write_snippets(self):
        write_snippets(self.dest / self.doc_gen_folder / self.snippet_files_folder, self._doc_gen.snippets)

    def run(self):
        logger.debug("Copying docgen files...")
        self.copy_doc_gen()
        _iam_fixup_metadata(self.dest)
        logger.debug("Collecting snippets...")
        self._doc_gen.collect_snippets()
        self._doc_gen = _iam_fixup_docgen(self._doc_gen)
        logger.debug("Writing snippets...")
        self.write_snippets()


def main():
    from argparse import ArgumentParser
    argparse = ArgumentParser()
    argparse.add_argument('--root', type=Path, default=Path())
    argparse.add_argument('--dest', type=Path)
    # Load a config from somewhere to get doc_gen_folder and snippets_files_folder
    args = argparse.parse_args()

    builder = Builder(args.root, args.dest)
    builder.run()


if __name__ == "__main__":
    main()
