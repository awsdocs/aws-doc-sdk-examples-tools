from dataclasses import dataclass
from pathlib import Path
from typing import List


class Command:
    pass


@dataclass
class CreatePrompts(Command):
    doc_gen_root: str 
    system_prompts: List[str]
    out_dir: str


@dataclass
class RunAilly(Command):
    batches: List[str]


@dataclass
class UpdateReservoir(Command):
    root: Path
    batches: List[str]
    packages: List[str]
