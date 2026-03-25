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
cmn_handler = utils.add_common_args(_parser, UTILS_PATH, proj_dir=PROJ_DIR)
args = _parser.parse_args()

test = {
    "a": {
        "b": 1,
        "c": [0, 1, 2],
    }
}
a = utils.get_nested(test, "a", rtn_type=str)
print(a)


def main() -> None:
    cfg = Configurator(app_name="cfgtest")
    dpath = "saved_data.test3.yaml"
    cmn_handler()
    if args.get_installs:
        os.chdir(PROJ_DIR)
        utils.get_poetry_installs()
        return

    options = {"a": "A", "b": "B", "c": "C"}

    sys.exit(
        embed(
            globals=globals(),
            locals=locals(),
            history_filename="jbutils_cli.history",
        )
    )


if __name__ == "__main__":
    main()
