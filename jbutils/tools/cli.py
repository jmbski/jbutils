"""CLI Testing tool for checking local functionality"""

import argparse
import json
import os
import re
import sys
from ptpython import embed


from dataclasses import dataclass

from ptpython import embed

from jbutils.config import Configurator
from jbutils import utils
from jbutils.console import JbuConsole
from jbutils.repl import ReplBase, SuggestFromLs

TOOL_DIR = os.path.dirname(__file__)
JBUTILS_DIR = os.path.dirname(TOOL_DIR)
PROJ_DIR = os.path.dirname(JBUTILS_DIR)
UTILS_PATH = os.path.join(JBUTILS_DIR, "utils", "utils.py")

_parser = argparse.ArgumentParser(description=__doc__)
_parser.add_argument(
    "--get-installs",
    "-i",
    action="store_true",
    help="Get poetry add command for jbutils packages",
)
_parser.add_argument(
    "--repl-mode",
    "-r",
    action="store_true",
    help="Run REPL test mode",
)
_parser.add_argument("--interactive", "-I", action="store_true")
cmn_handler = utils.add_common_args(_parser, UTILS_PATH, proj_dir=PROJ_DIR)
args = _parser.parse_args()


@dataclass
class TestRepl(ReplBase):
    def __post_init__(self) -> None:
        super().__post_init__()
        # self.add_command("test_cmd", self.test_cmd, help_txt="Test command")

        self.setup_cmds_2(*self.get_local_funcs())

    def test_cmd(self) -> None:
        """Simple test command"""
        user_input = self.input("Testing prompt: ", suggestions=SuggestFromLs())
        self.print(user_input)

    def print_output(self, msg: str = "test") -> None:
        """Simple print command

        Args:
            msg (str): Message to output
        """
        self.print(msg)

    def test_2(
        self, val: int, nums: list[int], add: bool = True, add2: bool = False
    ) -> None:
        """Test function with multiple args and a list

        Args:
            val (int): Starting number
            nums (list[int]): Numbers to apply val to and sum together
            add (bool, optional): If true, adds val to nums, else subtracts.
                Defaults to True.
            add2 (bool, optional): Additional flag for testing
        """
        total = sum([val + n if add else n - val for n in nums])
        self.print(f"Total: {total}")


def test_repl():
    test = TestRepl()
    test.run()


def main() -> None:
    cfg = Configurator(app_name="cfgtest")
    dpath = "saved_data.test3.yaml"
    cmn_handler()

    if args.interactive:
        sys.exit(
            embed(
                globals=globals(),
                locals=locals(),
                history_filename="jbutils_cli.history",
            )
        )

    if args.repl_mode:
        test_repl()

    if args.get_installs:
        os.chdir(PROJ_DIR)
        utils.get_poetry_installs()
        return


if __name__ == "__main__":
    main()
