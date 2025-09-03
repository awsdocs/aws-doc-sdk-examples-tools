from typing import Any, Callable, Dict, List, Optional, Sequence, Type

from aws_doc_sdk_examples_tools.lliam.domain import commands, errors
from aws_doc_sdk_examples_tools.lliam.service_layer import (
    create_prompts,
    dedupe_reservoir,
    update_doc_gen,
    run_ailly,
    unit_of_work,
)

# Only handling Commands for now.
Message = commands.Command


def handle(
    message: Any, uow: Optional[unit_of_work.FsUnitOfWork] = None
) -> Sequence[errors.DomainError]:
    if isinstance(message, commands.Command):
        return handle_command(message, uow)

    return [
        errors.CommandExecutionError(
            command_name="Unknown", message=f"{message} was not a Command"
        )
    ]


def handle_command(
    command: commands.Command, uow: Optional[unit_of_work.FsUnitOfWork]
) -> Sequence[errors.DomainError]:
    handler = COMMAND_HANDLERS.get(type(command))
    if not handler:
        return [
            errors.CommandExecutionError(
                command_name=command.name, message="Handler for not found."
            )
        ]
    return handler(command, uow)


COMMAND_HANDLERS: Dict[
    Type[commands.Command], Callable[..., Sequence[errors.DomainError]]
] = {
    commands.CreatePrompts: create_prompts.create_prompts,
    commands.RunAilly: run_ailly.handle_run_ailly,
    commands.UpdateReservoir: update_doc_gen.handle_update_reservoir,
    commands.DedupeReservoir: dedupe_reservoir.handle_dedupe_reservoir,
}
