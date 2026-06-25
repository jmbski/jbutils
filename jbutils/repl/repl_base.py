"""

#######################################################################

    Module Name: repl_base
    Description: Base class for REPL tools
    Author: Joseph Bochinski
    Date: 2024-12-16


#######################################################################
"""

# region Imports
from __future__ import annotations

import argparse
import grp
import inspect
import math
import os
import platformdirs
import pwd
import re
import shlex
import stat
import tempfile
import time

from dataclasses import dataclass, field
from enum import Enum, EnumType
from pathlib import Path
from typing import Any, Callable, Literal, get_type_hints

from prompt_toolkit import PromptSession
from prompt_toolkit.buffer import Buffer
from prompt_toolkit.document import Document
from prompt_toolkit.auto_suggest import AutoSuggest, Suggestion
from prompt_toolkit.history import FileHistory
from prompt_toolkit.completion import WordCompleter
from prompt_toolkit.styles import Style
from ptpython.repl import embed
from rich import pretty
from rich.console import Console
from rich.theme import Theme
from tabulate import tabulate

from jbutils import utils

from jbutils.types import ColorSystem
from jbutils.repl.cmd_meta import ReplCommand, CommandMeta

# endregion Imports


# region Classes


@dataclass
class ReplTheme(Theme):
    title: str = "bold cyan"
    prompt: str = "bold green"
    warn: str = "bold yellow"
    error: str = "bold red"
    cmd_name: str = "bold green"
    cmd_desc: str = "cyan"
    exit_kw: str = "bold green"
    exit_str: str = "cyan"
    greeting: str = "cyan"
    addl_styles: dict | None = None

    def __post_init__(self) -> None:
        styles = dict(vars(self))
        extras = styles.pop("addl_styles", {})
        if extras:
            styles.update(extras)
        super().__init__(styles)


@dataclass
class ReplBase:
    """Dataclass for CLI options"""

    debug_enabled: bool | None = None
    """Debug mode enabled"""

    title: str = ""
    """Title of the CLI REPL Prompt"""

    exit_keywords: list[str] = field(default_factory=list)
    """List of strings that cause the REPL to close, defaults to x, q, 
        exit, and quit"""

    init_prompt: str | list[str] = ""
    """Prompt to display at startup"""

    color_system: ColorSystem = "auto"
    """Color system for the rich console"""

    theme: ReplTheme | dict = field(default_factory=ReplTheme)

    console: Console = field(default_factory=Console)
    """ Rich Console instance """

    history: Path | str = field(default_factory=Path)
    """Path to the prompt history file"""

    temp_file: str | Path = field(default_factory=Path)
    """Path to prompt temporary file"""

    style: dict | Style = field(default_factory=dict)
    """Style for the prompt"""

    ignore_case: bool = False
    """Ignore case setting for the WordCompleter instance"""

    commands: dict[str, ReplCommand] = field(default_factory=dict)
    """Command dictionary for prompt_toolkit. Keys are command names,
        values are the corresponding description/help text"""

    docstring_format: str = "google"

    parent: ReplBase | dict | None = None

    session: PromptSession = field(default_factory=PromptSession)

    cmd_defs: dict[str, CommandMeta] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if isinstance(self.commands, dict):
            for cmd_name, cmd in self.commands.items():
                if isinstance(cmd, dict):
                    self.commands[cmd_name] = ReplCommand(**cmd)

        if self.debug_enabled is None:
            self.debug_enabled = False

        self.title = self.title or "CLI Tool"

        self.exit_keywords = self.exit_keywords or ["x", "q", "exit", "quit"]

        exit_kw_str = ", ".join(
            f'[exit_kw]"{kw}"[/exit_kw]' for kw in self.exit_keywords
        )
        exit_kw_pref = "Type one of " if len(self.exit_keywords) > 1 else "Type "
        exit_str = f"[exit_str]{exit_kw_pref}{exit_kw_str} to exit[/exit_str]"

        self.init_prompt = self.init_prompt or [
            f"[title]<<| {self.title} |>>[/title]",
            exit_str,
            '[greeting]Type [cmd_name]"help"[/cmd_name] to view available commands.[/greeting]',
        ]

        self.color_system = self.color_system or "truecolor"

        if isinstance(self.theme, dict):
            props = list(dict(vars(ReplTheme())).keys())
            init: dict[str, Any] = {"addl_styles": {}}
            for key, value in self.theme.items():
                if key in props:
                    init[key] = value
                else:
                    init["addl_styles"][key] = value

            self.theme = ReplTheme(**init)
        elif self.theme is None:
            self.theme = ReplTheme()

        self.console = Console(color_system=self.color_system, theme=self.theme)

        if isinstance(self.history, str):
            self.history = Path(self.history)

        if self.history == Path():
            history_name = f".{re.sub(r"\s+", "_", self.title.lower())}_history"
            self.history = Path(platformdirs.user_config_dir(history_name))

        hist_dir = self.history.parent

        if not hist_dir.exists():
            hist_dir.mkdir(parents=True, exist_ok=True)

        if isinstance(self.temp_file, str):
            self.temp_file = Path(self.temp_file)

        if self.temp_file == Path():
            self.temp_file = Path(tempfile.gettempdir()) / f".{self.title}_tmp"

        temp_dir = self.temp_file.parent
        if not temp_dir.exists():
            temp_dir.mkdir(parents=True, exist_ok=True)

        self.style = self.style or {
            "prompt": "bold green",
            "": "default",
        }
        if isinstance(self.style, dict):
            self.style = Style.from_dict(self.style)

        self.apply_def_cmds()

    def apply_def_cmds(self) -> None:
        """Add the descriptions for the help and exit commands"""
        base_cmds: dict[str, ReplCommand] = {
            "\\[help, h]": ReplCommand(help_txt="Display this help message again"),
        }
        if self.exit_keywords:
            exit_str = ", ".join(self.exit_keywords)
            base_cmds.update(
                {
                    f"\\[{exit_str}]": ReplCommand(help_txt="Exit tool"),
                }
            )

        base_cmds.update(self.commands)
        self.commands = base_cmds

    def get_cmd_names(self) -> list[str]:
        """Retrieve names of commands, parsing out the help/exit commands"""

        help_str = "[help, h]"
        exit_str = f'[{", ".join(self.exit_keywords or [])}]'
        names: list[str] = [
            name
            for name in self.commands.keys()
            if name not in [help_str, exit_str]
        ]
        names.extend(["help", "h"])
        names.extend(self.exit_keywords)
        return names

    def print(self, *args) -> None:
        """Shortcut to console.print"""
        self.console.print(*args)

    def input(self, *args, suggestions: AutoSuggest | None = None) -> str:
        """Shortcut to console.input"""

        if self.session:
            return self.session.prompt(*args, auto_suggest=suggestions)
        return self.console.input(*args)

    def input_int(self, *args, catch_invalid: bool = True) -> int:
        """Parse input as int"""

        user_input = self.input(*args).strip().split(".")[0].strip()

        if not catch_invalid:
            return int(user_input)

        while True:
            try:
                return int(user_input)
            except:
                self.print(f"Invalid input: `{user_input}`.")

                user_input = (
                    self.input("Enter a valid selection:")
                    .strip()
                    .split(".")[0]
                    .strip()
                )

    def input_bool(self, *args, true_list: list[str] | None = None) -> bool:
        """Parse input as bool"""
        true_list = true_list or ["y", "yes"]
        true_list = [val.lower() for val in true_list]

        user_input = self.input(*args)
        return user_input.strip().lower() in true_list

    def input_prefer_int(self, *args) -> int | str:
        """Parse input as int if possible, otherwise return the string"""
        if not args:
            return 0
        user_input = self.input(*args).strip().split(".")[0].strip()
        try:
            return int(user_input)
        except:
            return user_input

    def input_choice(self, *args, choices: list[str]) -> str:
        """Prompt for a choice from a list of options"""
        for idx, option in enumerate(choices, start=1):
            print(f"[{idx}]: {option}")
        choice = self.input_int(*args) - 1

        while choice < 0 or choice >= len(choices):
            print(f"Invalid selection ({choice+1}), enter valid selection:")
            choice = self.input_int(*args) - 1
        return choices[choice]

    def input_choice_dict(self, prompt: str, choices: dict) -> Any:
        """Similar to input_choice, but with more control over the options

        Args:
            prompt (str): String to print to the user
            choices (dict): Dict of choices; keys will be the displayed options, values will be the associated return value

        Returns:
            Any: Selected value
        """

        keys = list(choices.keys())
        for idx, choice_idx in enumerate(keys, start=1):
            print(f"[{idx}]: {choice_idx}")

        choice_idx = self.input_int(prompt) - 1

        while choice_idx < 0 or choice_idx >= len(choices):
            print(f"Invalid selection ({choice_idx+1}), enter valid selection:")
            choice_idx = self.input_int(prompt) - 1

        return choices[keys[choice_idx]]

    def input_obj_update(self, obj: dict[str, Any]) -> Any:

        prop_name = self.input_choice(
            "Select property to update: ", choices=list(obj.keys())
        )
        prop = obj[prop_name]

        if not prop:
            self.warn(f"{prop_name} is an invalid selection")
            return prop_name, None

        prompt = f"Enter value for {prop_name}: "
        value = prop
        if prop is str | list[str]:
            value = self.input(prompt)
        elif prop is int | list[int]:
            value = self.input_int(prompt)
        elif prop is bool:
            value = self.input_bool(prompt)
        elif isinstance(prop, EnumType):
            value = self.get_enum_val(prompt, prop)
        elif isinstance(prop, Enum):
            value = self.get_enum_val(prompt, type(prop))
        else:
            self.warn("Invalid property type")
            return prop_name, prop
        return prop_name, value

    def get_enum_val(self, prompt: str, enum_cls: EnumType):
        """Prompt the user to select an enum value

        Args:
            prompt (str): Prompt to display
            enum_cls (EnumType): Enum class to select from

        Returns:
            Enum: Selected enum value
        """

        options = dict(enum_cls.__members__)

        if len(options) == 1:
            return list(options.values())[0]
        else:
            return self.input_choice_dict(prompt, options)

    def debug(self, *args) -> None:
        """Print only if debug_enabled == True"""
        if self.debug_enabled:
            self.print(*args)

    def add_command(
        self,
        cmd_name: str,
        cmd_func: Callable | None = None,
        help_txt: str = "",
        use_parser: bool = False,
        description: str = "",
        # auto_suggest: AutoSuggest,
        **def_kwargs,
    ) -> ReplCommand:
        """Add a command to the REPL

        Args:
            cmd_name (str): Name of the command
            cmd_func (Callable, optional): Function to execute when called.
                Defaults to None.
            help_txt (str, optional): Help text to display from REPL help command.
                Defaults to "".
            use_parser (bool, optional): If true, adds an argparse.ArgumentParser
                to the new ReplCommand instance. Defaults to False.
            description (str, optional): Optional description for the
                ArgumentParser help text. Defaults to help_txt.
            def_args: Default arguments for the command function
            def_kwargs: Default keyword arguments for the command function

        Returns:
            ReplCommand: The new ReplCommand instance
        """

        new_cmd = ReplCommand(command=cmd_func, help_txt=help_txt)
        if use_parser:
            new_cmd.parser = argparse.ArgumentParser(
                description=description or help_txt,
            )
        if def_kwargs:
            new_cmd.def_kwargs = def_kwargs

        self.commands[cmd_name] = new_cmd
        return new_cmd

    def gen_command(
        self, cmd_name: str, hyphenate: bool = True
    ) -> ReplCommand | None:
        cmd: Callable | None = getattr(self, cmd_name, None)

        if not callable(cmd):
            return

        cmd_meta = CommandMeta(func=cmd, register_cmd=self.add_command)
        self.cmd_defs[cmd_name] = cmd_meta
        return cmd_meta.gen_command(hyphenate=hyphenate)

    def setup_cmds(self, *cmd_names: str) -> None:
        """Automatically configure commands based on the provided names
            The ReplCommand objects are populated based on function meta
            data retrieved from the provided function names
        Args:
            cmd_names (list[str]): List of class methods to convert to REPL commands
        """

        funcs: list[Callable] = [
            getattr(self, name)
            for name in cmd_names
            if hasattr(self, name) and callable(getattr(self, name))
        ]

        for func in funcs:
            help_text = func.__doc__ or ""
            name = func.__name__
            self.add_command(name, func, help_txt=help_text)

    def setup_cmds_2(self, *cmd_names: str, hyphenate: bool = True):
        for name in cmd_names:
            self.gen_command(name, hyphenate=hyphenate)

    def get_local_funcs(self, tgt_cls: type | None = None) -> list[str]:
        """Retrieve a list of local functions for this class

        Returns:
            list[str]: List of function names
        """

        base_funcs = [
            name
            for name in dir(ReplBase)
            if callable(getattr(ReplBase, name)) and not name.startswith("_")
        ]

        tgt_cls = tgt_cls or self.__class__

        return [
            name
            for name in dir(tgt_cls)
            if callable(getattr(tgt_cls, name))
            and not name.startswith("_")
            and name not in base_funcs
        ]

    def warn(self, msg: str) -> None:
        """Print a message to the REPL preformatted as a warning"""

        self.print(f"[warn]\\[WARNING]: {msg}[/warn]")

    def error(self, msg: str) -> None:
        """Print a message to the REPL preformatted as an error"""

        self.print(f"[error]\\[ERROR]: {msg}[/error]")

    def pretty_print(self, obj: Any) -> None:
        pretty.pprint(obj)

    def pwd(self) -> str:
        """Print out the current path location

        Returns:
            str: The current path
        """

        self.print(f"Current location: {os.getcwd()}")
        return os.getcwd()

    def cd(self, path: str = "..") -> str:
        """Move the terminal to a new path location

        Args:
            path (str, optional): Path to move to. Defaults to "..".

        Returns:
            str: The new location
        """

        try:
            os.chdir(path)
        except FileNotFoundError:
            self.warn(
                f"Path: {path} does not exist, remaining in current directory"
            )
        new_pwd = os.getcwd()
        self.print(f"New dir: {new_pwd}")
        return new_pwd

    def ls(self, path: str = ".") -> list[str]:
        """List metadata about the files/directories at the given path

        Args:
            path (str, optional): Path to list. Defaults to ".".

        Returns:
            list[str]: List of file and directory names at the location
        """

        utils.ls_liah(path)
        return os.listdir(path)

    def interactive(self, *args, **kwargs) -> None:
        """Starts an interactive session from within the class"""
        if kwargs:
            globals().update(kwargs)
        embed(
            globals(),
            locals(),
            history_filename=os.path.expanduser(f"~/.{self.title}_history"),
        )

    def show_help(self) -> None:
        """Print out the provided help text"""

        for cmd_name, cmd in self.commands.items():
            self.print(
                f"[cmd_name]{cmd_name}:[/cmd_name] [cmd_desc]{cmd.help_txt}[/cmd_desc]"
            )

    def print_prompt(self) -> None:
        """Prints the prompt message if defined"""

        if isinstance(self.init_prompt, list):
            for line in self.init_prompt:
                self.print(line)
        else:
            self.print(self.init_prompt)

    def run(self) -> None:
        """Initiates a REPL with the provided configuration"""

        completer = WordCompleter(
            self.get_cmd_names(), ignore_case=self.ignore_case
        )

        if isinstance(self.style, dict):
            self.style = Style.from_dict(self.style)

        self.session = PromptSession(
            completer=completer,
            style=self.style or Style(self.style.items()),
            history=FileHistory(self.history),
            tempfile=str(self.temp_file),
            auto_suggest=SuggestFromLs(),
        )

        self.print_prompt()

        while True:
            try:
                user_input = self.session.prompt("> ", complete_while_typing=True)

                if user_input.lower() in ["help", "h"]:
                    self.show_help()
                elif user_input.lower() in self.exit_keywords:
                    self.warn(f"Exiting REPL ({self.title})...")
                    break
                else:
                    args = shlex.split(user_input)
                    if not args:
                        self.warn("No command provided")
                        continue

                    cmd = self.commands.get(args.pop(0))

                    if not cmd:
                        self.warn("Invalid command")
                        continue

                    if cmd.command:
                        if cmd.parser:
                            if args and args[0] in [
                                "help",
                                "h",
                                "-h",
                                "--help",
                            ]:
                                cmd.parser.print_help()
                                continue
                            cmd_args = cmd.parser.parse_args(args)
                            self.print(cmd_args)
                            cmd.command(**vars(cmd.parser.parse_args(args)))
                        else:
                            if cmd.def_kwargs:
                                cmd.command(*args, **cmd.def_kwargs)
                            else:
                                cmd.command(*args)
                    else:
                        self.warn("No function provided for command")
            except (EOFError, KeyboardInterrupt):
                self.warn(f"Exiting REPL ({self.title})...")
                break
            except argparse.ArgumentError as e:
                self.error(f"Error parsing arguments: {e}")
            except argparse.ArgumentTypeError as e:
                self.error(f"Error parsing arguments: {e}")

        if isinstance(self.parent, ReplBase):
            self.parent.print_prompt()


class SuggestFromLs(AutoSuggest):

    def get_suggestion(
        self, buffer: Buffer, document: Document
    ) -> Suggestion | None:
        files = os.listdir()

        # Consider only the last line for the suggestion.
        text = document.text.rsplit("\n", 1)[-1]
        split = text.split(" ", 1)
        if len(split) <= 1:
            return None
        text = split[1]
        if text.strip():
            for item in files:
                if item.lower().startswith(text.lower()):
                    return Suggestion(item[len(text) :])
        return None


# endregion Classes


# region Functions


def setvar(name: str, var: Any) -> None:
    globals()[name] = var


def setfunc(func: Callable) -> None:
    globals()[func.__name__] = func


# endregion Functions
