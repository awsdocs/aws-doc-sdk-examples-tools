from pathlib import Path
from subprocess import run
from typing import List

import typer

from aws_doc_sdk_examples_tools.agent.make_prompts import main as make_prompts
from aws_doc_sdk_examples_tools.agent.parse_json_files import main as parse_json_files
from aws_doc_sdk_examples_tools.agent.update_doc_gen import main as update_doc_gen

app = typer.Typer()

AILLY_DIR = ".ailly_iam_policy"
AILLY_DIR_PATH = Path(AILLY_DIR)
IAM_UPDATES_PATH = AILLY_DIR_PATH / "iam_updates.json"


def get_ailly_files(dir: Path):
    return [
        file
        for file in dir.iterdir()
        if file.is_file() and file.name.endswith(".ailly.md")
    ]


@app.command()
def update(iam_tributary_root: str, system_prompts: List[str] = []):
    doc_gen_root = Path(iam_tributary_root)
    make_prompts(
        doc_gen_root=doc_gen_root, system_prompts=system_prompts, out=AILLY_DIR_PATH
    )
    run(["npx", "@ailly/cli", "--root", AILLY_DIR])
    file_paths = get_ailly_files(AILLY_DIR_PATH)
    parse_json_files(file_paths=file_paths, out=IAM_UPDATES_PATH)
    update_doc_gen(doc_gen_root=doc_gen_root, iam_updates_path=IAM_UPDATES_PATH)


if __name__ == "__main__":
    app()
