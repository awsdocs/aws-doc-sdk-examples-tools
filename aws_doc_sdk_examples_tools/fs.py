from abc import ABC, abstractmethod
from dataclasses import dataclass
from fnmatch import fnmatch
from os import listdir
from pathlib import Path
from stat import S_ISREG
from typing import Dict, Generator, List


@dataclass(frozen=True)
class Stat:
    path: Path
    exists: bool
    is_file: bool

    @property
    def is_dir(self):
        return self.exists and not self.is_file


class Fs(ABC):
    @abstractmethod
    def glob(self, path: Path, glob: str) -> Generator[Path, None, None]:
        pass

    @abstractmethod
    def read(self, path: Path) -> str:
        pass

    @abstractmethod
    def readlines(self, path: Path) -> List[str]:
        pass

    @abstractmethod
    def write(self, path: Path, content: str):
        pass

    @abstractmethod
    def stat(self, path: Path) -> Stat:
        pass

    @abstractmethod
    def mkdir(self, path: Path):
        pass

    @abstractmethod
    def list(self, path: Path) -> List[Path]:
        pass


class PathFs(Fs):
    def glob(self, path: Path, glob: str) -> Generator[Path, None, None]:
        return path.glob(glob)

    def read(self, path: Path) -> str:
        with path.open("r") as file:
            return file.read()

    def readlines(self, path: Path) -> List[str]:
        with path.open("r") as file:
            return file.readlines()

    def write(self, path: Path, content: str):
        with path.open("w") as file:
            file.write(content)

    def stat(self, path: Path) -> Stat:
        if path.exists():
            stat = path.stat()
            return Stat(path, True, S_ISREG(stat.st_mode))
        else:
            return Stat(path, False, False)

    def mkdir(self, path: Path):
        path.mkdir(parents=True, exist_ok=True)

    def list(self, path: Path) -> List[Path]:
        if self.stat(path).is_file:
            return []
        return [path / name for name in listdir(path)]


class RecordFs(Fs):
    def __init__(self, fs: Dict[Path, str]):
        self.fs = fs

    def glob(self, path: Path, glob: str) -> Generator[Path, None, None]:
        path_s = str(path)
        for key in self.fs.keys():
            key_s = str(key)
            if key_s.startswith(path_s):
                if fnmatch(key_s, glob):
                    yield key

    def read(self, path: Path) -> str:
        return self.fs[path]

    def readlines(self, path: Path) -> List[str]:
        content = self.fs[path]
        return content.splitlines(keepends=True)

    def write(self, path: Path, content: str):
        base = str(path.parent)
        assert any(
            [str(key).startswith(base) for key in self.fs]
        ), "No parent folder, this will probably fail without a call to mkdir in a real file system!"
        self.fs[path] = content

    def stat(self, path: Path):
        if path in self.fs:
            return Stat(path, True, True)
        for item in self.fs.keys():
            if str(item).startswith(str(path)):
                return Stat(path, True, False)
        return Stat(path, False, False)

    def mkdir(self, path: Path):
        self.fs.setdefault(path, "")

    def list(self, path: Path) -> List[Path]:
        return [item for item in self.fs.keys() if item.parent == path]


fs = PathFs()
