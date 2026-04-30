"""CLI Tool to manage Poetry project versions"""

import argparse
import os
import re

""" from ..general_modules import utils
from ..general_modules.utils import e_open """

from jbutils import utils
from jbutils.console import JbuConsole

VERSION_PATTERN = r"\d+\.\d+\.\d+"

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument(
    "--path", help="URI path to the project directory. Defaults to pwd"
)
parser.add_argument(
    "--get", "-g", action="store_true", help="Retrieve the current version number"
)
parser.add_argument(
    "--tag", "-t", action="store_true", help="tag name of the next version number"
)
parser.add_argument("--set", "-s", help="Specific version number to set")
parser.add_argument(
    "--major",
    "-M",
    action="store_true",
    help="Increment the major version number (minor and patch set to 0)",
)
parser.add_argument(
    "--minor",
    "-m",
    action="store_true",
    help="Increment the minor version number (patch set to 0)",
)
parser.add_argument(
    "--patch", "-p", action="store_true", help="Increment the patch version number"
)

args = parser.parse_args()


def get_version_numbers(version: str) -> tuple[int, ...]:
    """Get version numbers from version string"""

    return tuple(int(num) for num in version.split("."))


def get_pyproject() -> tuple[dict, str]:

    dir_path = args.path or os.getcwd()
    pyproject_file = os.path.join(dir_path, "pyproject.toml")

    if not os.path.exists(pyproject_file):
        raise FileNotFoundError("pyproject.toml not found")

    return utils.read_file(pyproject_file, cast=dict), pyproject_file


def get_vers_str(pyproject: dict | None = None) -> str:
    if pyproject is None:
        pyproject, _ = get_pyproject()

    return utils.get_nested(pyproject, "tool.poetry.version")


def main():
    """Main function"""

    pyproject, pyproject_file = get_pyproject()

    current_version = get_vers_str(pyproject)

    if not current_version:
        raise ValueError("Version not found in pyproject.toml")

    if not re.match(VERSION_PATTERN, current_version):
        raise ValueError(
            "Invalid version format in pyproject.toml, you will need to change format or update manually. Please use x.x.x"
        )

    major, minor, patch = get_version_numbers(current_version)

    if args.tag:
        print(f"v{major}.{minor}.{patch+1}")
        return
    new_version = None

    if args.set:
        set_version = args.set.strip()
        if not re.match(VERSION_PATTERN, set_version):
            raise ValueError("Invalid version format, please use x.x.x")

        new_version = set_version
    else:
        if args.major:
            major += 1
            minor = 0
            patch = 0
        elif args.minor:
            minor += 1
            patch = 0
        elif args.patch:
            patch += 1
        else:
            raise ValueError("Invalid arguments, please use -M, -m, -p or -s")

        new_version = f"{major}.{minor}.{patch}"

    JbuConsole.print(f"Current version: {current_version}")
    JbuConsole.print(f"New version: {new_version}")
    if new_version == current_version:
        print("Versions are the same, no changes made")
        return

    JbuConsole.print("Updating pyproject.toml")
    pyproject["tool"]["poetry"]["version"] = new_version

    utils.write_file(pyproject_file, pyproject)


if __name__ == "__main__":
    main()
