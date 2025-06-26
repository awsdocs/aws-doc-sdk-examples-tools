from pathlib import Path
from subprocess import run
from typing import List
import time
from datetime import timedelta, datetime

import logging
import typer

from aws_doc_sdk_examples_tools.agent.make_prompts import make_prompts
from aws_doc_sdk_examples_tools.agent.process_ailly_files import process_ailly_files
from aws_doc_sdk_examples_tools.agent.update_doc_gen import update_doc_gen
from aws_doc_sdk_examples_tools.yaml_writer import prepare_write, write_many

logging.basicConfig(
    level=logging.INFO, filename=f"lliam-run-{datetime.now()}.log", filemode="w"
)
logger = logging.getLogger(__name__)

app = typer.Typer()

AILLY_DIR = ".ailly_iam_policy"
AILLY_DIR_PATH = Path(AILLY_DIR)
IAM_UPDATES_PATH = AILLY_DIR_PATH / "iam_updates.json"


def format_duration(seconds: float) -> str:
    td = timedelta(seconds=seconds)
    return str(td).zfill(8)


@app.command()
def update(
    iam_tributary_root: str,
    system_prompts: List[str] = [],
    skip_generation: bool = False,
) -> None:
    """
    Generate new IAM policy metadata for a tributary.
    """
    doc_gen_root = Path(iam_tributary_root)

    if not skip_generation:
        make_prompts(
            doc_gen_root=doc_gen_root,
            system_prompts=system_prompts,
            out_dir=AILLY_DIR_PATH,
            language="IAMPolicyGrammar",
        )

        batch_dirs = [
            d.name
            for d in AILLY_DIR_PATH.iterdir()
            if d.is_dir() and d.name.startswith("batch_")
        ]

        if batch_dirs:
            total_start_time = time.time()

            for batch_dir in sorted(batch_dirs):
                batch_start_time = time.time()

                cmd = [
                    "ailly",
                    "--max-depth",
                    "10",
                    "--root",
                    AILLY_DIR,
                    str(batch_dir),
                ]
                logger.info(f"Running {cmd}")
                run(cmd)

                batch_end_time = time.time()
                batch_duration = batch_end_time - batch_start_time
                batch_num = batch_dir.replace("batch_", "")
                logger.info(
                    f"[TIMECHECK] Batch {batch_num} took {format_duration(batch_duration)} to run"
                )

            total_end_time = time.time()
            total_duration = total_end_time - total_start_time
            num_batches = len(batch_dirs)
            logger.info(
                f"[TIMECHECK] {num_batches} batches took {format_duration(total_duration)} to run"
            )

    logger.info("Processing generated content")
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
