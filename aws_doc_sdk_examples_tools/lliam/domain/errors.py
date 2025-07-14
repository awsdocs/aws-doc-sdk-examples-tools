from dataclasses import dataclass


@dataclass
class DomainError:
    pass


@dataclass
class CommandExecutionError(DomainError):
    command_name: str
    message: str
