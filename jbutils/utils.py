"""Collection of common utils functions for personal repeated use"""

import argparse
import csv
import json
import inspect
import io
import os
import re
import shlex
import subprocess
import sys
import traceback
import fnmatch

# _vi = sys.version_info
# if _vi.major >= 3 and _vi.minor >= 11:
try:
    import tomllib
except:
    import tomli as tomllib
import toml

from pathlib import Path
from platform import platform

from collections.abc import Callable, Iterable, Iterator
from dataclasses import dataclass
from time import time
from typing import Any, Optional, overload, Type

import json5
import jsonlines
import pymupdf

from jsonlines.jsonlines import JSONValue
from PIL import Image, ImageFile
from PIL.ImageFile import ImageFile
from pymupdf import Document
from ruamel.yaml import YAML
from ruamel.yaml.comments import CommentedMap, CommentedSeq
from ruamel.yaml.tokens import CommentToken
from ruamel.yaml.scalarstring import LiteralScalarString, ScalarString
from typing_extensions import TypeGuard

from jbutils.console import JbuConsole
from jbutils.types import (
    CommandArg,
    FileReadType,
    T,
    Patterns,
    PathJoiner,
    DataPath,
    DataPathList,
    SubReturn,
    StrVarArgsFn,
)

yaml = YAML()
yaml.indent = 2

Predicate = Callable[[T], bool]
IMAGE_EXTS = [
    ".png",
    ".jpg",
    ".jpeg",
    ".gif",
    ".bmp",
    ".tiff",
    ".webp",
    ".avif",
    ".svg",
    ".ico",
]

SUPPROTED_EXTS = [
    "csv",
    "json",
    "jsonl",
    "yaml",
    "yml",
] + IMAGE_EXTS


class Consts:
    encoding: str = "UTF-8"


# pylint: disable=C0103
@dataclass
class SubReturns:
    """Enum class for SubReturn values"""

    OUT: SubReturn = "out"
    ERR: SubReturn = "err"
    BOTH: SubReturn = "both"


# pylint: enable=C0103

p_join = os.path.join
p_exists = os.path.exists


def set_encoding(enc: str) -> None:
    Consts.encoding = enc


def set_yaml_indent(indent: int) -> None:
    yaml.indent = 2


@overload
def read_file(
    path: str | Path,
    /,
    mode: str = "r",
    *,
    encoding: str | None = Consts.encoding,
    default_val: Any = None,
    as_lines: bool = False,
    as_dicts: bool = False,
    allow_json5: bool = True,
    cast: None = None,
    **kwargs: Any,
) -> FileReadType: ...


# when cast is not provided, we return the "raw" union


@overload
def read_file(
    path: str | Path,
    /,
    mode: str = "r",
    *args,
    encoding: str | None = Consts.encoding,
    default_val: Any = None,
    as_lines: bool = False,
    as_dicts: bool = False,
    allow_json5: bool = True,
    cast: Callable[..., T],
    **kwargs: Any,
) -> T: ...


# when cast is provided, return type is T


def read_file(
    path: str | Path,
    /,
    mode: str = "r",
    *args,
    encoding: str | None = Consts.encoding,
    default_val: Any = None,
    as_lines: bool = False,
    as_dicts: bool = False,
    allow_json5: bool = True,
    cast: Callable[..., T] | None = None,
    **kwargs: Any,
) -> FileReadType | T:
    """Read a file and optionally transform its result.

    Args:
        path (str): The path to the file
        mode (str, optional): IO mode to use. Defaults to "r".
        encoding (str, optional): Encoding format to use.
            Defaults to "latin-1".
        default_val (Any, optional): Value to return if the file is not found.
            Defaults to None.
        as_lines (bool, optional): If reading a regular text file,
            True will return the value of readlines() instead of read().
            Defaults to False.
        as_dicts (bool, optional): If reading a csv file, return lines as
            dicts if True
        cast (type, optional): Optional callable used to transform the
            raw result into a specific type.
        *args (args, optional): Special args to pass to the associated
            reader class
        **kwargs (kwargs, optional): Special kwargs to pass to the associated
            reader class

    Returns:
        The raw file content (str, dict, list, ImageFile, or Document) or the
        transformed value if `cast` is provided.
    """

    default_val = default_val or {}

    if not os.path.exists(path):
        print(f"Warning: Path '{path}' does not exist")
        return default_val

    ext = get_ext(str(path)).lower()
    if ext == ".toml":
        mode = "rb"
        encoding = None

    rtn_value = default_val

    with open(path, mode, encoding=encoding, *args, **kwargs) as fs:
        match ext:
            case ".yaml" | ".yml":
                rtn_value = yaml.load(stream=fs)
            case ".json":
                try:
                    rtn_value = json.load(fs)
                except json.JSONDecodeError as e:
                    if allow_json5:
                        fs.seek(0)
                        rtn_value = json5.load(fs)
                    else:
                        raise e

            case ".jsonl":
                rtn_value = [item for item in jsonlines.Reader(fs).iter()]
            case ".jsonc" | ".code-workspace":
                rtn_value = json5.load(fs)
            case ".toml":
                rtn_value = tomllib.load(fs)
            case ".csv":
                data = list(csv.reader(fs))
                if as_dicts:
                    if not data:
                        rtn_value = []

                    cols = data.pop(0)

                    if not data:
                        rtn_value = []

                    rtn_value = [dict(zip(cols, vals)) for vals in data]
                else:
                    rtn_value = data
            case ".pdf":
                rtn_value = pymupdf.open(fs)
            case _:
                if ext.lower() in IMAGE_EXTS:
                    rtn_value = Image.open(fs)
                if as_lines:
                    rtn_value = fs.readlines()
                else:
                    rtn_value = fs.read()

    if cast is not None:
        return cast(rtn_value)
    return rtn_value


def to_jsonl(items: list, check_serial: bool = True) -> list:
    new_items = []
    for item in items:
        if isinstance(item, str):
            # If it's a str, just try to convert to a json serialized
            # structure, since a raw str isn't a valid jsonl line value
            new_items.append(json.loads(item))
        else:
            # Otherwise, alternate dumps and loads to make sure item is
            # serializable if check_serial is true, otherwise just use the raw value
            value = json.loads(json.dumps(item)) if check_serial else item
            new_items.append(value)
    return new_items


def ext_supported(ext: str, data: Any = None) -> bool:
    return ext in SUPPROTED_EXTS or isinstance(data, ImageFile)


def write_file(
    path: str | Path,
    data: Any,
    mode: str = "w",
    encoding: str | None = Consts.encoding,
    indent: int = 4,
    *args,
    **kwargs,
) -> None:
    """Write text to a file

    Args:
        path (str): The path to the file
        data (Any): The data to write
        mode (str, optional): Read/write mode. Defaults to "w".
        encoding (str, optional): Encoding to write with. Defaults to ENCODING.
        indent (int, optional): Indent to apply if JSON. Defaults to 4.
        *args (args, optional): Special args to pass to the associated
            writer class
        **kwargs (kwargs, optional): Special kwargs to pass to the associated
            writer class
    """

    ext = get_ext(str(path)).lower()

    wr_args = args if not ext_supported(ext, data) else ()
    wr_kwargs = kwargs if not ext_supported(ext, data) else {}

    with open(path, mode, encoding=encoding, *wr_args, **wr_kwargs) as fs:
        match ext:
            case ".yml" | ".yaml":
                yaml.dump(data, fs, *args, **kwargs)
            case ".json":
                json.dump(data, fs, indent=indent, *args, **kwargs)
            case ".jsonl":
                writer = jsonlines.Writer(fs, *args, **kwargs)
                if isinstance(data, list):
                    lines = to_jsonl(data)
                else:
                    lines = to_jsonl([data])
                writer.write_all(lines)
            case ".toml":
                # tomllib.dump(fs)
                toml.dump(data, fs)
            case _:
                if isinstance(data, ImageFile):
                    data.save(fs, *args, **kwargs)
                if isinstance(data, list):
                    fs.writelines(data)
                else:
                    fs.write(str(data))


def get_ext(path: str) -> str:
    """Get the file extension from a path

    Args:
        path (str): The path to the file

    Returns:
        str: The file extension including the dot, or an empty string if no extension exists
    """

    return os.path.splitext(path)[1]


def replace_ext(path: str | Path, ext: str) -> str:
    """Replace the file extension in a path with a new one
    Args:
        path (str): The path to the file
        ext (str): The new file extension, including the dot
    Returns:
        str: The path with the new file extension
    """

    return os.path.splitext(path)[0] + ext


def strip_ext(path: str | Path) -> str:
    """Get the file name without the extension from a path

    Args:
        path (str): The path to the file

    Returns:
        str: The file name without the extension, or an empty string if no name exists
    """

    return os.path.splitext(os.path.basename(path))[0]


def get_os_sep() -> str:
    if platform() == "Windows":
        return "\\"
    else:
        return "/"


def split_path(path: str | Path, keep_ext: bool = True) -> list[str]:
    path_split = []
    head, tail = os.path.split(path)
    if not tail:
        return [head.replace(get_os_sep(), "")]

    if not keep_ext:
        tail = strip_ext(tail)

    path_split.append(tail)
    max_depth = 32
    count = 0
    while tail and count < max_depth:
        head, tail = os.path.split(head)
        if tail:
            path_split.insert(0, tail)
        count += 1
    return path_split


def find(items: list, value: Any) -> int:
    """A 'not in list' safe version of list.index()

    Args:
        items (list): List to search
        value (Any): Value to search for

    Returns:
        int: Index of the first instance of value, or -1 if not found
    """

    try:
        return items.index(value)
    except ValueError:
        return -1


def list_get(items: list[T], *preds: Predicate[T]) -> T | None:
    """Searches a list for the first item that matches all predicates

    Args:
        items (list[T]): List of items to search

    Returns:
        T | None: First matching item, or None if no items matched
    """

    for item in items:
        if all(pred(item) for pred in preds):
            return item
    return None


def list_get_all(items: list[T], *preds: Predicate[T]) -> list[T]:
    """Searches a list for all items that match all predicates

    Args:
        items (list[T]): List of items to search

    Returns:
        list[T]: List of items that matched the predicates.
    """

    return [item for item in items if all(pred(item) for pred in preds)]


def update_list_values(
    items: list[Any],
    new_items: list[Any],
    sort: bool = False,
    sort_func: Optional[Predicate[Any]] = None,
    reverse: bool = False,
) -> list[Any]:
    """Add new items to a list and sort it

    Args:
        items (list[Any]): Items to add to
        new_items (list[Any]): Items to add
        sort (Callable[[Any], bool], optional): Custom sort function. Defaults to None.
        reverse (bool, optional): If true, sort order is reversed. Defaults to False.

    Returns:
        list[Any]: The updated list
    """

    for item in new_items:
        if item not in items:
            items.append(item)

    if sort:
        if sort_func:
            items.sort(key=sort_func, reverse=reverse)
        else:
            items.sort(reverse=reverse)

    return items


def remove_list_values(
    items: list[Any],
    del_items: list[Any],
    sort: bool = False,
    sort_func: Optional[Predicate[Any]] = None,
    reverse: bool = False,
) -> list[Any]:
    """Remove items from a list and sort it

    Args:
        items (list[Any]): Items to remove from
        del_items (list[Any]): Items to remove
        sort (Callable[[Any], bool], optional): Custom sort function. Defaults to None.
        reverse (bool, optional): If true, sort order is reversed. Defaults to False.

    Returns:
        list[Any]: The updated list
    """

    for item in del_items:
        if item in items:
            items.remove(item)
    if sort:
        if sort_func:
            items.sort(key=sort_func, reverse=reverse)
        else:
            items.sort(reverse=reverse)

    return items


def get_stack_trace(depth: int = -2) -> str:
    # Get the current stack frame
    stack = traceback.format_stack()

    return "\n".join(stack[:depth])


def print_stack_trace(depth: int = -2):
    # Get the current stack frame

    JbuConsole.print(get_stack_trace(depth))


def debug_print(*args):
    """Print debug statements with a newline before and after"""

    strings = list(args)
    strings.insert(0, "\n")
    strings.append("\n")
    print(*strings)


def pretty_print(obj: Any) -> None:
    """Prints a JSON serializable object with indentation"""

    print(json.dumps(obj, indent=4))


def copy_to_clipboard(text):
    process = subprocess.Popen(
        ["xclip", "-selection", "clipboard"], stdin=subprocess.PIPE
    )
    process.communicate(input=text.encode("utf-8"))


def dedupe_list(items: list) -> list:
    new_list = []
    for item in items:
        if item not in new_list:
            new_list.append(item)
    return new_list


def dedupe_in_place(items: list) -> list:
    uniques = []
    dupes = []

    for item in items:
        if item not in uniques:
            uniques.append(item)
        else:
            dupes.append(item)

    for item in dupes:
        items.remove(item)

    return dupes


def get_keys(obj: dict, keys: Optional[list[str]] = None) -> Any:
    if not isinstance(obj, dict):
        return keys

    keys = keys or []
    keys.extend(obj.keys())
    for value in obj.values():
        get_keys(value, keys)

    return keys


def parse_cfg_key(key: list[str] | str, trim_exts: bool = True) -> list[str]:
    if isinstance(key, str):
        key = key.split(".")
        if not trim_exts:
            if len(key) >= 2:
                ext = key.pop()
                fname = key.pop()
                key.append(f"{fname}{ext}")

    return key


def parse_data_path(
    key: DataPath, sep: str = ".", split_exts: bool = True
) -> DataPathList:

    if isinstance(key, int):
        return [key]
    if isinstance(key, str):
        key = key.split(sep)
        if not split_exts and len(key) >= 2:
            ext = key.pop()
            fname = key.pop()
            key.append(f"{fname}.{ext}")
    return key


def parse_int(value: Any) -> int | None:
    try:
        return int(value)
    except ValueError:
        return None


IDX_RE = re.compile(r"\[\s*(-?\d+)\s*\]")


def is_idx_key(key_part: str | int) -> bool:
    if isinstance(key_part, int):
        return False
    return IDX_RE.search(key_part) is not None or key_part == "+"


def get_idx_key(key_part: str | int) -> str | int:
    key_part = str(key_part)
    matches = IDX_RE.findall(key_part)
    if matches:
        key_part = int(matches[0])

    return key_part


@overload
def get_nested(
    obj: dict | list,
    path: DataPath,
    /,
    default: Any = None,
    sep: str = ".",
    *,
    rtn_type: None = None,
) -> Any: ...


@overload
def get_nested(
    obj: dict | list,
    path: DataPath,
    /,
    default: Any = None,
    sep: str = ".",
    *,
    rtn_type: Callable[..., T],
) -> T: ...


def get_nested(
    obj: dict | list,
    path: DataPath,
    /,
    default: Any = None,
    sep: str = ".",
    *,
    rtn_type: Callable[..., T] | None = None,
) -> Any | T:
    """Get a nested value from a dictionary or list

    Args:
        obj (dict | list): The object to get the value from
        path (list[str] | str): The path to the value
        default (Any, optional): The default value to return if the path is not found.
            Defaults to None.
        sep (str, optional): Separator to split string with if path is str.
            Defaults to "."

    Returns:
        Any: The value at the path or the default value
    """

    """ if isinstance(path, str):
        path = path.split(sep) """
    path = parse_data_path(path, sep)

    def get_t_value(value: Any) -> Any | T:
        if rtn_type is not None:
            return rtn_type(value)
        return value

    if not path:
        return get_t_value(default)

    if len(path) == 1:
        result = None
        key = get_idx_key(path[0])
        is_int = isinstance(key, int)
        if isinstance(obj, dict):
            result = obj.get(str(key), obj.get(key, default))

        elif isinstance(obj, list) and is_int:
            item = None
            if key < len(obj):
                item = obj[key]
            if item is None:
                item = default

            result = item
        return get_t_value(result)

    next_key = get_idx_key(path.pop(0))

    if isinstance(obj, list):
        if obj and isinstance(next_key, int):
            if next_key < len(obj):
                return get_nested(
                    obj[next_key], path, default, sep, rtn_type=rtn_type
                )
        return get_t_value(default)

    if str(next_key) not in obj and next_key not in obj:
        return get_t_value(default)

    return get_nested(obj[next_key], path, default, sep, rtn_type=rtn_type)


def delete_nested(obj: dict | list, path: DataPath, sep: str = ".") -> None:
    """Delete a nested value from a dictionary or list

    Args:
        obj (dict | list): The object to delete the value from
        path (list[str] | str): The path to the value
        sep (str, optional): Separator to split string with if path is str.
            Defaults to "."
    """

    """ if isinstance(path, str):
        path = path.split(sep) """
    path = parse_data_path(path, sep)

    if not path:
        return

    if len(path) == 1:
        debug_print(obj)

        key = get_idx_key(path[0])

        if isinstance(obj, (dict, CommentedMap)):
            obj.pop(key, None)
        elif isinstance(obj, (list, CommentedSeq)):
            if obj and isinstance(key, int):
                if key < len(obj):
                    obj.pop(key)
            """ elif path[0] in obj:
                debug_print("removing", path[0])
                obj.remove(path[0]) """
    else:
        next_key = get_idx_key(path.pop(0))
        if isinstance(obj, list):
            if isinstance(next_key, int):
                if next_key < len(obj):
                    delete_nested(obj[next_key], path)
        elif next_key in obj or str(next_key) in obj:
            delete_nested(obj[next_key], path)


def _set_next_append(
    obj: list,
    path: DataPathList,
    value: Any,
    debug: bool = False,
    overwrite: bool = False,
) -> None:
    """Set a value in a nested object when the index is out of bounds

    Args:
        obj (list): Object to set the value in
        path (list[str]): Path to the value
        key (str | int): Key to set the value at
        value (Any): Value to set
        debug (bool, optional): Flag to enable debug statements. Defaults to False.
        overwrite (bool, optional): Flag to overwite existing data along path.
            Defaults to False.
    """
    if debug:
        debug_print("out of bounds", "inserting new value", f"path[0] = {path[0]}")

    new_val = [] if is_idx_key(path[0]) else {}
    obj.append(new_val)

    if debug:
        debug_print("blank inserted", obj)

    set_nested(
        obj=obj[-1], path=path, value=value, debug=debug, overwrite=overwrite
    )


def _set_next_list_item(
    obj: list,
    path: DataPathList,
    key: int,
    value: Any,
    debug: bool = False,
    overwrite: bool = False,
) -> None:
    """Iterate through the next item in a list or dictionary

    Args:
        obj (list): Object to set the value in
        path (list[str]): Path to the value
        key (str | int): Key to set the value at
        value (Any): Value to set
        debug (bool, optional): Flag to enable debug statements. Defaults to False.
        overwrite (bool, optional): Flag to overwite existing data along path.
            Defaults to False.
    """

    if not path:
        return

    sub = obj[key]

    if not sub or not isinstance(sub, (dict, list)):
        if debug:
            debug_print("sub is None or not an object", "creating new sub")
        if overwrite:
            if is_idx_key(path[0]):
                obj[int(key)] = []
            else:
                obj[int(key)] = {}
        else:
            return

    set_nested(
        obj=obj[key],
        path=path,
        value=value,
        debug=debug,
        overwrite=overwrite,
    )


def _set_final_prop(obj: dict | list, path: DataPathList, value: Any) -> None:
    """Set a value in a nested object at the final path

    Args:
        obj (dict | list): Object to set the value in
        path (list[str]): Path to the value
        value (Any): Value to set
    """

    key = get_idx_key(path[0])

    if isinstance(obj, dict):
        obj[key] = value
    elif isinstance(obj, list):
        if isinstance(key, int) and key < len(obj):
            obj[key] = value
        else:
            obj.append(value)


def _set_next_nested(
    obj: dict,
    path: DataPathList,
    value: Any,
    key: str | int,
    debug: bool = False,
    overwrite: bool = False,
) -> None:
    """Set a value in a nested object

    Args:
        obj (dict | list): Object to set the value in
        path (list[str]): Path to the value
        value (Any): Value to set
        key (str | int): Key to set the value at
        debug (bool, optional): Flag to enable debug statements. Defaults to False.
        overwrite (bool, optional): Flag to overwite existing data along path.
            Defaults to False.
    """

    sub = obj.get(key)

    if debug:
        debug_print("obj is dict", "sub:", sub)

    if not sub or not isinstance(sub, (dict, list)):
        if debug:
            debug_print("sub is None or not an object", "creating new sub")

        if is_idx_key(path[0]):  # and create_lists:
            obj[key] = []
        else:
            obj[key] = {}

        if debug:
            debug_print("new sub created", obj)

    prop = obj.get(key)
    if isinstance(prop, (list | dict)):
        set_nested(
            obj=prop,
            path=path,
            value=value,
            debug=debug,
            overwrite=overwrite,
        )


def set_nested(
    obj: dict | list,
    path: DataPath,
    value: Any,
    debug: bool = False,
    overwrite: bool = False,
    sep: str = ".",
) -> None:
    """Set a nested value in a dictionary or list

    Args:
        obj (dict | list): The object to set the value in
        path (list[str] | str): The path to the value
        value (Any): The value to set
        debug (bool, optional): Flag to enable debug statements. Defaults to False.
        overwrite (bool, optional): Flag to overwite existing data along path.
            Defaults to False.
    """

    path = parse_data_path(path, sep)

    if debug:
        print_stack_trace()
        debug_print("starting function")
        pretty_print({"obj": obj, "path": path, "value": value})

    if not path:
        return

    if len(path) == 1:
        _set_final_prop(obj, path, value)
    else:
        key = get_idx_key(path.pop(0))

        if debug:
            debug_print("key", key)

        if isinstance(obj, list):
            if debug:
                debug_print("obj is list", "key < len", int(key) < len(obj))
            if obj and isinstance(key, int) and key < len(obj):
                _set_next_list_item(
                    obj=obj,
                    path=path,
                    key=key,
                    value=value,
                    debug=debug,
                    overwrite=overwrite,
                )
            elif isinstance(key, int) or key == "+":
                _set_next_append(
                    obj=obj,
                    path=path,
                    value=value,
                    debug=debug,
                    overwrite=overwrite,
                )
        elif isinstance(obj, dict):
            _set_next_nested(
                obj=obj,
                path=path,
                value=value,
                key=key,
                debug=debug,
                overwrite=overwrite,
            )


def cmdx(
    cmd: list[str] | str, rtrn: SubReturn = "out", print_out: bool = True
) -> str | tuple[str, str]:
    """Executes a command and returns the output or error

    Args:
        cmd (list[str] | str): - A list of strings that make up the command or a string
            that will be split by spaces
        rtrn (SubReturn, optional): What outputs to return. If both, it will return a
            tuple of (stdout, stderr)Defaults to 'out'.

    Returns:
        str | tuple[str, str]: The output of the command or a tuple of (stdout, stderr)
    """

    if isinstance(cmd, str):
        cmd = shlex.split(cmd)

    try:
        process = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            encoding="utf-8",
            check=True,
        )
    except subprocess.CalledProcessError as e:
        # Print and handle the errors here if needed
        process = e

    stdout = process.stdout
    stderr = process.stderr
    if print_out:
        if stdout:
            print(stdout)
        if stderr:
            print("\nERROR:\n", stderr)

    if rtrn == "out":
        return process.stdout
    if rtrn == "err":
        return process.stderr

    return process.stdout, process.stderr


def join_paths(
    root: str | Path, paths: list[str | Path] | list[Path] | list[str]
) -> list[str]:
    """Join each path in paths with the root str

    Args:
        root (str): Directory root path
        paths (list[str]): list of paths to join with root

    Returns:
        list[str]: List of os.path.join(root, path) for all paths
    """

    return [os.path.join(root, path) for path in paths]


def list_paths(
    path: str | Path,
    *predicates: Predicate[str],
    rtn_abs: bool = False,
    check_abs: bool = True,
) -> list[str]:
    """Extension of os.listdir(path) that allows you to pre-filter the
        results with a list of predicate functions

    Args:
        path (str): Path to inspect
        predicates ([list[Predicate[str]]  |  Predicate[str]], optional):
            A function or list of functions used to filter the returned
            path names. Defaults to [].
        rtn_abs (bool, optional): Return paths as absolute if True, else
            only file names. Defaults to False.
        check_abs (bool, optional): Check predicates against absolute paths
            else check against file names. Defaults to True.

    Returns:
        list[str]: List of files/directories at the location that pass
            all predicates, returns [] if path is invalid
    """

    if not os.path.exists(path) or not os.path.isdir(path):
        return []

    fnames = os.listdir(path)
    fullpaths = join_paths(path, fnames)
    match_paths: list[str] = []
    for i, fpath in enumerate(fullpaths):
        if all(
            predicate(fpath if check_abs else fnames[i]) for predicate in predicates
        ):

            match_paths.append(fpath if rtn_abs else fnames[i])
    return match_paths


def rm_dirs(
    dir_path: str | Path,
    ignored: Patterns | None = None,
    use_glob: bool = True,
) -> None:
    """
    Deletes all contents of a directory, optionally ignoring files or directories
    matching any of the given patterns.

    Args:
        dir_path (str): The path to the directory whose contents will be
            deleted.
        ignored (Patterns, optional): A list of glob patterns or compiled
            regexes to skip. Defaults to []
        use_glob (bool, optional): If True, treat patterns as glob-style
            strings. If False, treat them as regex. Defaults to True
    """
    dir_path = Path(dir_path)
    ignored = ignored or []

    def should_ignore(path: Path) -> bool:
        rel_path = str(path.relative_to(dir_path))
        for pattern in ignored:
            if isinstance(pattern, str) and use_glob:
                if fnmatch.fnmatch(rel_path, pattern):
                    return True
            elif isinstance(pattern, re.Pattern):
                if pattern.search(rel_path):
                    return True
        return False

    for root, dirs, files in os.walk(dir_path, topdown=False):
        for name in files:
            full_path = Path(root) / name
            if not should_ignore(full_path):
                full_path.unlink()
        for name in dirs:
            full_path = Path(root) / name
            if not should_ignore(full_path):
                try:
                    full_path.rmdir()  # only removes if empty
                except OSError:
                    pass  # ignore non-empty directories


def get_local_funcs(tgt_cls: type, *base_classes: type) -> list[str]:
    """Get all local functions of a class that are not inherited from its
        base classes. This function retrieves all callable attributes of
        the target class that do not start with an underscore and are not
        present in the base classes.

    Args:
        tgt_cls (type): The target class from which to retrieve functions.
        *base_classes (type): Base classes to exclude inherited functions from.

    Returns:
        list[str]: A list of function names that are defined in the target class
            and not inherited from the base classes.
    """

    base_funcs = set()

    for base_cls in base_classes:
        base_funcs.update(
            [
                name
                for name in dir(base_cls)
                if callable(getattr(base_cls, name)) and not name.startswith("_")
            ]
        )

    return [
        name
        for name in dir(tgt_cls)
        if callable(getattr(tgt_cls, name))
        and not name.startswith("_")
        and name not in base_funcs
    ]


def parse_csv_line(csv_str: str) -> list[str]:
    """Parses a single-line CSV string into a list of strings using ISO-like rules."""
    reader = csv.reader(io.StringIO(csv_str))
    return next(reader)


def to_csv_line(items: list[str]) -> str:
    """Serializes a list of strings into a single CSV-formatted string."""
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(items)
    return output.getvalue().strip("\r\n")


def add_common_args(
    parser: argparse.ArgumentParser,
    proj_path: str,
    proj_dir: str = "",
    overrides: dict[str, CommandArg] | None = None,
) -> Callable[..., argparse.Namespace]:
    overrides = overrides or {}

    cmd_args: list[CommandArg] = [
        overrides.get(
            "code",
            CommandArg(
                "--code",
                "-c",
                "store_true",
                help="Open the source file for this tool in VS Code",
            ),
        ),
        overrides.get(
            "cd",
            CommandArg(
                "--cd",
                "-C",
                "store_true",
                help="Copy a cd command to the project directory to the clipboard",
            ),
        ),
    ]

    for arg in cmd_args:

        parser.add_argument(*arg.name_or_flags, action=arg.action, help=arg.help)

    proj_path = os.path.abspath(proj_path)
    proj_dir = proj_dir or os.path.dirname(os.path.dirname(proj_path))

    def handle_common() -> argparse.Namespace:
        code, cd = cmd_args
        args = parser.parse_args()
        arg_props = vars(args)
        if arg_props.get(code.arg_name):
            cmdx(f'code "{proj_path}"')
            sys.exit(0)
        if arg_props.get(cd.arg_name):
            path = proj_dir
            copy_to_clipboard(f"cd {path}")
            sys.exit(0)
        return args

    return handle_common


def reg_funcs_as_actions(
    env: dict, parser: argparse.ArgumentParser, *predicates: Predicate
) -> None:
    # funcs: list[tuple[str, Callable]] = []
    available_funcs: list[str] = []

    def is_func(val: Any) -> TypeGuard[Callable]:
        if not inspect.isfunction(val):
            return False
        if not hasattr(val, "__name__"):
            return False
        if val.__name__ == reg_funcs_as_actions.__name__:
            return False

        return all(pred(val) for pred in predicates)

    for key, value in env.items():
        if is_func(value):
            # funcs.append((key, value))
            available_funcs.append(key)

    parser.add_argument(
        "action",
        help="action to take",
        choices=available_funcs,
    )
    parser.add_argument(
        "remaining", nargs=argparse.REMAINDER, help="Remaining arguments"
    )


def fix_yaml_strs(val: Any) -> Any:
    if isinstance(val, str):
        return LiteralScalarString(ScalarString(val))
    if isinstance(val, dict):
        for key, value in val.items():
            val[key] = fix_yaml_strs(value)
    elif isinstance(val, list):
        for i, item in enumerate(val):
            val[i] = fix_yaml_strs(item)
    return val


def extract_comment(data: CommentedMap | CommentedSeq) -> str:
    comment: list[CommentToken] = data._yaml_get_pre_comment()
    if not comment:
        return ""
    return comment[0].value


def joiner(path: str | Path = "", abs_path: bool = False) -> StrVarArgsFn:
    if abs_path:
        return lambda *x: os.path.abspath(os.path.join(path, *x))
    return lambda *x: os.path.join(path, *x)


def profile(func: Callable, *args, **kwargs) -> float:
    start = time()
    func(*args, **kwargs)
    return round((time() - start) * 1000, 3)


def get_poetry_installs(incldue_vers: bool = True):
    out: str = cmdx("poetry show", print_out=False)  # type: ignore
    lines = out.split("\n")

    line_re = re.compile(r"\s+")

    cmd = "poetry add "

    for line in lines:
        matches = line_re.split(line)
        if len(matches) < 2:
            continue

        pkg = matches[0]
        version = matches[1]
        if incldue_vers:
            cmd += f"{pkg}=={version} "
        else:
            cmd += f"{pkg} "

    try:
        copy_to_clipboard(cmd)
        print("Poetry installs command copied to clipboard")
    except:
        print(cmd)


p_exists.__doc__ = os.path.exists.__doc__
