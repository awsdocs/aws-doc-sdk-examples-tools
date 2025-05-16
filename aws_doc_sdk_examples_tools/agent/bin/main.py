from pathlib import Path
from subprocess import run
from typing import List

import typer

from aws_doc_sdk_examples_tools.agent.make_prompts import make_prompts
from aws_doc_sdk_examples_tools.agent.process_ailly_files import process_ailly_files
from aws_doc_sdk_examples_tools.agent.update_doc_gen import update_doc_gen
from aws_doc_sdk_examples_tools.yaml_writer import prepare_write, write_many

app = typer.Typer()

AILLY_DIR = ".ailly_iam_policy"
AILLY_DIR_PATH = Path(AILLY_DIR)
IAM_UPDATES_PATH = AILLY_DIR_PATH / "iam_updates.json"


@app.command()
def update(iam_tributary_root: str, system_prompts: List[str] = []) -> None:
    """
    Generate new IAM policy metadata for a tributary.
    """
    doc_gen_root = Path(iam_tributary_root)
    make_prompts(
        doc_gen_root=doc_gen_root,
        system_prompts=system_prompts,
        out_dir=AILLY_DIR_PATH,
        language="IAMPolicyGrammar",
    )
    run(["npx", "@ailly/cli", "--root", AILLY_DIR])

    process_ailly_files(
        input_dir=str(AILLY_DIR_PATH), output_file=str(IAM_UPDATES_PATH)
    )

    doc_gen = update_doc_gen(
        doc_gen_root=doc_gen_root, iam_updates_path=IAM_UPDATES_PATH
    )

    writes = prepare_write(doc_gen.examples)
    write_many(doc_gen_root, writes)


if __name__ == "__main__":
    app()
