from pathlib import Path
from typing import List, Optional
from typing_extensions import Annotated
from datetime import datetime
import logging
import typer

from aws_doc_sdk_examples_tools.lliam.config import AILLY_DIR, BATCH_PREFIX
from aws_doc_sdk_examples_tools.lliam.domain import commands, errors
from aws_doc_sdk_examples_tools.lliam.service_layer import messagebus, unit_of_work

logging.basicConfig(
    level=logging.INFO,
    filename=f"lliam-run-{datetime.now().strftime('%Y%m%d_%H%M%S')}.log",
    filemode="w",
)

logger = logging.getLogger(__name__)
app = typer.Typer(name="Lliam")


@app.command()
def create_prompts(iam_tributary_root: str, system_prompts: List[str] = []):
    doc_gen_root = iam_tributary_root
    cmd = commands.CreatePrompts(
        doc_gen_root=doc_gen_root,
        system_prompts=system_prompts,
        out_dir=AILLY_DIR,
    )
    uow = unit_of_work.FsUnitOfWork()
    errors = messagebus.handle(cmd, uow)
    handle_domain_errors(errors)


@app.command()
def run_ailly(
    batches: Annotated[
        Optional[str],
        typer.Option(help="Batch names to process (comma-separated list)"),
    ] = None,
    packages: Annotated[
        Optional[str], typer.Option(help="Comma delimited list of packages to update")
    ] = None,
) -> None:
    """
    Run ailly to generate IAM policy content and process the results.
    If batches is specified, only those batches will be processed.
    If batches is omitted, all batches will be processed.
    If packages is specified, only those packages will be processed.
    """
    requested_batches = parse_batch_names(batches)
    package_names = parse_package_names(packages)
    cmd = commands.RunAilly(batches=requested_batches, packages=package_names)
    errors = messagebus.handle(cmd)
    handle_domain_errors(errors)


@app.command()
def update_reservoir(
    iam_tributary_root: str,
    batches: Annotated[
        Optional[str],
        typer.Option(help="Batch names to process (comma-separated list)"),
    ] = None,
    packages: Annotated[
        Optional[str], typer.Option(help="Comma delimited list of packages to update")
    ] = None,
) -> None:
    """
    Update the doc_gen reservoir with processed IAM policy updates.
    If batches is specified, only those batch directories will be processed.
    If batches is omitted, all available update files will be processed.
    """
    doc_gen_root = Path(iam_tributary_root)
    batch_names = parse_batch_names(batches)
    package_names = parse_package_names(packages)
    cmd = commands.UpdateReservoir(
        root=doc_gen_root, batches=batch_names, packages=package_names
    )
    errors = messagebus.handle(cmd)
    handle_domain_errors(errors)


@app.command()
def dedupe_reservoir(
    iam_tributary_root: str,
    packages: Annotated[
        Optional[str], typer.Option(help="Comma delimited list of packages to update")
    ] = None,
) -> None:
    """
    Enumerate fields that must be unique (e.g. title_abbrev)
    """
    doc_gen_root = Path(iam_tributary_root)
    package_names = parse_package_names(packages)
    cmd = commands.DedupeReservoir(root=doc_gen_root, packages=package_names)
    errors = messagebus.handle(cmd)
    handle_domain_errors(errors)


def handle_domain_errors(errors: List[errors.DomainError]):
    if errors:
        for error in errors:
            logger.error(error)
        typer.Exit(code=1)


def parse_batch_names(batch_names_str: Optional[str]) -> List[str]:
    """
    Parse batch names from a comma-separated string.
    """
    if not batch_names_str:
        return []

    batch_names = []

    for name in batch_names_str.split(","):
        maybe_batch_name = name.strip()
        assert maybe_batch_name.startswith(BATCH_PREFIX)
        batch_names.append(maybe_batch_name)

    return batch_names


def parse_package_names(package_names_str: Optional[str]) -> List[str]:
    if not package_names_str:
        return []

    return [n.strip() for n in package_names_str.split(",")]


if __name__ == "__main__":
    app()
