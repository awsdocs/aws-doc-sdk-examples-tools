from typing import Callable, Dict, Optional, Type

from aws_doc_sdk_examples_tools.lliam.domain import commands
from aws_doc_sdk_examples_tools.lliam.service_layer import (
    create_prompts,
    update_doc_gen,
    run_ailly,
    unit_of_work,
)

# Only handling Commands for now.
Message = commands.Command


def handle(message: commands.Command, uow: Optional[unit_of_work.FsUnitOfWork] = None):
    queue = [message]

    while queue:
        message = queue.pop(0)
        if isinstance(message, commands.Command):
            return handle_command(message, uow)
        else:
            raise Exception(f"{message} was not a Command")


def handle_command(command: commands.Command, uow: Optional[unit_of_work.FsUnitOfWork]):
    handler = COMMAND_HANDLERS[type(command)]
    errors = handler(command, uow)
    return errors


COMMAND_HANDLERS: Dict[Type[commands.Command], Callable] = {
    commands.CreatePrompts: create_prompts.create_prompts,
    commands.RunAilly: run_ailly.handle_run_ailly,
    commands.UpdateReservoir: update_doc_gen.handle_update_reservoir,
}
