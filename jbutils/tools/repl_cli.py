"""CLI path for Replbase repo"""

import argparse
import os

from pathlib import Path

from jbutils import jbutils
from rich.console import Console

DIR = Path(__file__).parent
SRC_PATH = DIR / "repl_base.py"


def main() -> None:
    """Main function"""

    parser = argparse.ArgumentParser(description=__doc__)
    parse_args = jbutils.add_common_args(parser, SRC_PATH)

    args = parse_args()

    console = Console()
    val = console.input("Enter a value [1]: (y/n)\n")
    console.print(val)


if __name__ == "__main__":
    main()
