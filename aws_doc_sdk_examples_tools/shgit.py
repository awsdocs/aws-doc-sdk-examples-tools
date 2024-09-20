from pathlib import Path
from subprocess import run
from typing import Optional


def make_long_flags(flags: dict[str, str]) -> list[str]:
    return [f"--{key}={val}" for key, val in flags.items()]


class Sh:
    def __init__(self,
                 args: Optional[str | list[str]] = None,
                 check=True,
                 capture_output=False,
                 cwd: str | bytes | Path = Path("."),
                 log=False):
        if args is None:
            self.args = []
        elif isinstance(args, str):
            self.args = [args]
        else:
            self.args = args
        self.check = check
        self.capture_output = capture_output
        self.cwd: str | bytes | Path = cwd
        self.log = log

    def __call__(self,
                 *args: str,
                 capture_output=False,
                 check=None,
                 cwd: Optional[str | bytes | Path] = None,
                 **kwargs: str):
        check = check or self.check
        cwd = cwd or self.cwd
        capture_output = capture_output or self.capture_output
        long_args = make_long_flags(kwargs)
        cmd: list[str] = [*self.args, *args, *long_args]
        if self.log:
            print(cmd)
        return run(cmd,
                   capture_output=capture_output,
                   check=check,
                   shell=False,
                   cwd=cwd)

    def __getattr__(self, arg: str):
        return Sh(
            [*self.args, arg],
            self.check,
            self.capture_output,
            self.cwd,
            self.log
            )


sh = Sh()
git = Sh('git')
