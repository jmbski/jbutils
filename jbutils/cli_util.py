"""Utility functions for handling CLI commands, similar to a REPL but as one-offs"""

from typing import Any

from rich.console import Console
from rich.theme import Theme


CNSL_THEME = Theme(
    {
        "title": "bold cyan",
        "prompt": "bold green",
        "warn": "bold yellow",
        "error": "bold red",
        "cmd_name": "bold green",
        "cmd_desc": "cyan",
        "exit_kw": "bold green",
        "exit_str": "cyan",
        "greeting": "cyan",
    }
)
console = Console(color_system="truecolor", theme=CNSL_THEME)


def print(*args, **kwargs) -> None:
    console.print(*args, **kwargs)


def input(*args) -> str:
    """Shortcut to console.input"""

    return console.input(*args)


def warn(msg: str) -> None:
    """Print a message to the console preformatted as a warning"""

    print(f"[warn]\\[WARNING]: {msg}[/warn]")


def error(msg: str) -> None:
    """Print a message to the console preformatted as an error"""

    print(f"[error]\\[ERROR]: {msg}[/error]")


def input_int(*args) -> int:
    """Parse input as int"""

    user_input = input(*args).strip().split(".")[0].strip()

    return int(user_input)


def input_bool(*args, true_list: list[str] | None = None) -> int:
    """Parse input as bool"""
    true_list = true_list or ["y", "yes"]
    true_list = [val.lower() for val in true_list]

    user_input = input(*args)
    return user_input.strip().lower() in true_list


def input_prefer_int(*args) -> int | str:
    """Parse input as int if possible, otherwise return the string"""
    if not args:
        return 0
    user_input = input(*args).strip().split(".")[0].strip()

    return int(user_input)


def input_choice(*args, choices: list[str]) -> str:
    """Prompt for a choice from a list of options"""
    for idx, choice in enumerate(choices):
        print(f"[{idx+1}]: {choice}")
    choice = input_int(*args) - 1

    while 0 < choice or choice >= len(choices):
        print(f"Invalid selection ({choice+1}), enter valid selection:")
        choice = input_int(*args)
    return choices[choice]


def input_choice_dict(prompt: str, choices: dict) -> Any:
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

    choice_idx = input_int(prompt) - 1

    while choice_idx < 0 or choice_idx >= len(choices):
        print(f"Invalid selection ({choice_idx+1}), enter valid selection:")
        choice_idx = input_int(prompt) - 1

    return choices[keys[choice_idx]]
