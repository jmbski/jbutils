"""Utility functions for outputting to the console"""

from typing import Any, Optional, TextIO

from rich import print
from rich.style import Style
from rich.text import TextType
from rich.console import Console, JustifyMethod, OverflowMethod
from rich.theme import Theme

from jbutils.consts import RuntimeGlobals
from jbutils.types import ColorSystem
from jbutils.models import ConsoleTheme


THEME = ConsoleTheme()


class JbuConsole:
    console: Console = Console(color_system="truecolor", theme=THEME)

    shell_prompt: str = "\n> "
    append_shell_prompt: bool = True

    _theme: Theme | ConsoleTheme = THEME
    _color_system: ColorSystem = "truecolor"

    @classmethod
    def _reset(cls) -> None:

        cls.console = Console(color_system=cls._color_system, theme=cls._theme)

    @classmethod
    def set_theme(cls, theme: dict | Theme | ConsoleTheme) -> None:
        if isinstance(theme, dict):
            theme = Theme(theme)
        cls._theme = theme
        cls._reset()

    @classmethod
    def set_color_system(cls, color_system: ColorSystem) -> None:
        cls._color_system = color_system
        cls._reset()

    @classmethod
    def log(cls, level: str, *msgs, **kwargs) -> None:
        cls.print(f"[{level}]\\[{level.upper()}]:[/{level}]", *msgs, **kwargs)

    @classmethod
    def debug(cls, *msgs, **kwargs) -> None:
        if RuntimeGlobals.debug:
            cls.log("debug", *msgs, **kwargs)

    @classmethod
    def verbose(cls, *msgs, **kwargs) -> None:
        if RuntimeGlobals.verbose:
            cls.log("verbose", *msgs, **kwargs)

    @classmethod
    def info(cls, *msgs, **kwargs) -> None:
        cls.log("info", *msgs, **kwargs)

    @classmethod
    def warn(cls, *msgs, **kwargs) -> None:
        cls.log("warn", *msgs, **kwargs)

    @classmethod
    def error(cls, *msgs, **kwargs) -> None:
        cls.log("error", *msgs, **kwargs)

    @classmethod
    def success(cls, *msgs, **kwargs) -> None:
        cls.log("success", *msgs, **kwargs)

    @classmethod
    def pprint(cls, *msgs, **kwargs) -> None:
        cls.pprint(*msgs, **kwargs)

    @classmethod
    def print(
        cls,
        *objects: Any,
        sep: str = " ",
        end: str = "\n",
        style: str | Style | None = None,
        justify: JustifyMethod | None = None,
        overflow: OverflowMethod | None = None,
        no_wrap: bool | None = None,
        emoji: bool | None = None,
        markup: bool | None = None,
        highlight: bool | None = None,
        width: int | None = None,
        height: int | None = None,
        crop: bool = True,
        soft_wrap: bool | None = None,
        new_line_start: bool = False,
    ) -> None:
        """Print to the console.

        Args:
            objects (positional args): Objects to log to the terminal.
            sep (str, optional): String to write between print data. Defaults to " ".
            end (str, optional): String to write at end of print data. Defaults to "\\\\n".
            style (Union[str, Style], optional): A style to apply to output. Defaults to None.
            justify (str, optional): Justify method: "default", "left", "right", "center", or "full". Defaults to ``None``.
            overflow (str, optional): Overflow method: "ignore", "crop", "fold", or "ellipsis". Defaults to None.
            no_wrap (Optional[bool], optional): Disable word wrapping. Defaults to None.
            emoji (Optional[bool], optional): Enable emoji code, or ``None`` to use console default. Defaults to ``None``.
            markup (Optional[bool], optional): Enable markup, or ``None`` to use console default. Defaults to ``None``.
            highlight (Optional[bool], optional): Enable automatic highlighting, or ``None`` to use console default. Defaults to ``None``.
            width (Optional[int], optional): Width of output, or ``None`` to auto-detect. Defaults to ``None``.
            crop (Optional[bool], optional): Crop output to width of terminal. Defaults to True.
            soft_wrap (bool, optional): Enable soft wrap mode which disables word wrapping and cropping of text or ``None`` for
                Console default. Defaults to ``None``.
            new_line_start (bool, False): Insert a new line at the start if the output contains more than one line. Defaults to ``False``.
        """

        cls.console.print(
            *objects,
            sep=sep,
            end=end,
            style=style,
            justify=justify,
            overflow=overflow,
            no_wrap=no_wrap,
            emoji=emoji,
            markup=markup,
            highlight=highlight,
            width=width,
            height=height,
            crop=crop,
            soft_wrap=soft_wrap,
            new_line_start=new_line_start,
        )

    @classmethod
    def input(
        cls,
        prompt: TextType = "",
        *,
        markup: bool = True,
        emoji: bool = True,
        password: bool = False,
        stream: Optional[TextIO] = None,
    ) -> str:
        """Displays a prompt and waits for input from the user. The prompt may contain color / style.

        It works in the same way as Python's builtin :func:`input` function and provides elaborate line editing and history features if Python's builtin :mod:`readline` module is previously loaded.

        Args:
            prompt (Union[str, Text]): Text to render in the prompt.
            markup (bool, optional): Enable console markup (requires a str prompt). Defaults to True.
            emoji (bool, optional): Enable emoji (requires a str prompt). Defaults to True.
            password: (bool, optional): Hide typed text. Defaults to False.
            stream: (TextIO, optional): Optional file to read input from (rather than stdin). Defaults to None.

        Returns:
            str: Text read from stdin.
        """

        if cls.append_shell_prompt and not str(prompt).endswith(cls.shell_prompt):
            prompt += cls.shell_prompt

        return cls.console.input(
            prompt, markup=markup, emoji=emoji, password=password, stream=stream
        )

    @classmethod
    def input_int(cls, *args, catch_invalid: bool = True) -> int:
        """Parse input as int"""

        user_input = cls.input(*args).strip().split(".")[0].strip()

        if not catch_invalid:
            return int(user_input)

        while True:
            try:
                return int(user_input)
            except:
                cls.print(f"Invalid input: `{user_input}`.")

                user_input = (
                    cls.input("Enter a valid selection:")
                    .strip()
                    .split(".")[0]
                    .strip()
                )

    @classmethod
    def input_bool(cls, *args, true_list: list[str] | None = None) -> int:
        """Parse input as bool"""
        true_list = true_list or ["y", "yes"]
        true_list = [val.lower() for val in true_list]

        user_input = cls.input(*args)
        return user_input.strip().lower() in true_list

    @classmethod
    def input_prefer_int(cls, *args) -> int | str:
        """Parse input as int if possible, otherwise return the string"""
        if not args:
            return 0
        user_input = cls.input(*args).strip().split(".")[0].strip()
        try:
            return int(user_input)
        except:
            return user_input

    @classmethod
    def input_choice(cls, *args, choices: list[str]) -> str:
        """Prompt for a choice from a list of options"""
        for idx, option in enumerate(choices, start=1):
            print(f"[{idx}]: {option}")
        choice = cls.input_int(*args) - 1

        while choice < 0 or choice >= len(choices):
            print(f"Invalid selection ({choice+1}), enter valid selection:")
            choice = cls.input_int(*args) - 1
        return choices[choice]

    @classmethod
    def input_choice_dict(cls, prompt: str, choices: dict) -> Any:
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

        choice_idx = cls.input_int(prompt) - 1

        while choice_idx < 0 or choice_idx >= len(choices):
            print(f"Invalid selection ({choice_idx+1}), enter valid selection:")
            choice_idx = cls.input_int(prompt) - 1

        return choices[keys[choice_idx]]
