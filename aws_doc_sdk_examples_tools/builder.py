from dataclasses import dataclass, field
import logging
from pathlib import Path

from aws_doc_sdk_examples_tools.doc_gen import DocGen
from aws_doc_sdk_examples_tools.fs import Fs, PathFs
from aws_doc_sdk_examples_tools.snippets import write_snippets

logging.basicConfig(level=logging.INFO)

logger = logging.getLogger(Path(__file__).name)


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
        logger.debug("Collecting snippets...")
        self._doc_gen.collect_snippets()
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
