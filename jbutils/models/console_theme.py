"""Module containing the ConsoleTheme class model"""

from dataclasses import dataclass

from rich.theme import Theme


@dataclass
class ConsoleTheme(Theme):
    """Model for defining a custom theme for the rich package"""

    debug: str = "bold sky_blue1"
    verbose: str = "bold light_slate_grey"
    info: str = "bold blue"
    warn: str = "bold orange3"
    error: str = "bold red"
    success: str = "bold green"
    title: str = "bold cyan"
    prompt: str = "bold green"
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
