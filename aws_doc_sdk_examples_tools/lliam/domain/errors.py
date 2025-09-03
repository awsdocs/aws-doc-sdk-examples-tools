from dataclasses import dataclass


@dataclass(frozen=True)
class DomainError:
    message: str


@dataclass(frozen=True)
class CommandExecutionError(DomainError):
    command_name: str

    def __repr__(self):
        return f"[{self.command_name}] {self.message}"
