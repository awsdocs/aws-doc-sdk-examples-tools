from dataclasses import dataclass
from pathlib import Path
from typing import List


@dataclass(frozen=True)
class Command:
    @property
    def name(self):
        return self.__class__.__name__


@dataclass(frozen=True)
class CreatePrompts(Command):
    doc_gen_root: str
    system_prompts: List[str]
    out_dir: str


@dataclass(frozen=True)
class RunAilly(Command):
    batches: List[str]
    packages: List[str]


@dataclass(frozen=True)
class UpdateReservoir(Command):
    root: Path
    batches: List[str]
    packages: List[str]


@dataclass(frozen=True)
class DedupeReservoir(Command):
    root: Path
    packages: List[str]
