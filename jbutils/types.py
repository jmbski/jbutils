"""Common types for the jbutils package"""

import re

from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path
from typing import (
    Any,
    Generic,
    Iterable,
    Literal,
    Optional,
    Pattern,
    Protocol,
    runtime_checkable,
    Sequence,
    TypeVar,
)

from PIL.ImageFile import ImageFile
from pymupdf import Document
from ruamel.yaml.comments import CommentedMap, CommentedSeq, Comment


# General Typing
T = TypeVar("T")
R = TypeVar("R")

OptStr = Optional[str]
OptInt = Optional[int]
OptFloat = Optional[float]
OptDict = Optional[dict]
OptList = Optional[list]
Opt = Optional[T]

FileReadType = str | dict | list | ImageFile | Document


# Function Types
Predicate = Callable[[T], bool]
Function = Callable[..., Any]
TFunction = Callable[..., T]

# Miscellaneous
Patterns = Sequence[str | Pattern[str]]
DataPathList = list[str] | list[str | int] | list[int]
DataPath = DataPathList | str | int

SubReturn = Literal["out", "err", "both"]
""" String literal type representing the output choices for cmdx """


class ClassProperty(Generic[T, R]):
    """A read-only class-level property descriptor."""

    def __init__(self, fget: Callable[[type[T]], R]):
        self.fget = fget

    def __get__(self, obj: Any, cls: type[T] | None = None) -> R:
        if cls is None:
            return self  # type: ignore[return-value]
        return self.fget(cls)


class StrVarArgsFn(Protocol):
    def __call__(self, *args: str) -> str: ...


@runtime_checkable
class PathJoiner(Protocol):
    """Factory function that assembles a QIcon instance"""

    def __call__(self, path: str | Path, abs_path: bool = ...) -> StrVarArgsFn: ...


class JbConfigType(Protocol):

    @property
    def debug(self) -> bool: ...

    @property
    def verbose(self) -> bool: ...

    @property
    def use_rich_console(self) -> bool: ...

    @property
    def log_fmt_std(self) -> str: ...

    @property
    def log_fmt_rich(self) -> str: ...

    @property
    def root_log_handlers(self) -> list[str]: ...

    @property
    def log_handler_map(self) -> dict[str, list[str]]: ...


ColorSystem = Literal["auto", "standard", "256", "truecolor", "windows"]


@dataclass
class CommandArg:
    name: str = ""
    flag: str = ""
    action: str = ""
    nargs: str | int | None = None
    const: Any = None
    default: Any = None
    arg_type: type | None = None
    choices: Iterable | None = None
    required: bool = False
    help: str | None = None
    metavar: str | tuple[str, ...] | None = None
    dest: str | None = None
    version: str | None = None

    name_or_flags: list[str] = field(default_factory=list)
    arg_name: str = ""

    def __post_init__(self) -> None:
        ws_re = re.compile(r"\s+")
        self.name = ws_re.sub("-", self.name.strip())
        self.name_or_flags.append(self.name)
        if self.flag:
            self.name_or_flags.append(self.flag)

        prefix_re = re.compile(r"^-+")
        space_re = re.compile(r"[-_ ]+")
        self.arg_name = prefix_re.sub("", self.name)
        self.arg_name = space_re.sub("_", self.arg_name)


__all__ = [
    "ClassProperty",
    "ColorSystem",
    "CommandArg",
    "Comment",
    "CommentedMap",
    "CommentedSeq",
    "FileReadType",
    "JbConfigType",
    "OptStr",
    "OptInt",
    "OptFloat",
    "OptDict",
    "OptList",
    "Opt",
    "PathJoiner",
    "Patterns",
    "Predicate",
    "R",
    "Function",
    "SubReturn",
    "StrVarArgsFn",
    "TFunction",
    "T",
]
