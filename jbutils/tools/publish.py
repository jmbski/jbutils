from jbutils import utils
from jbutils.console import JbuConsole
from jbutils.tools import vmgr


def publish():
    version = list(vmgr.get_version_numbers(vmgr.get_vers_str()))
    version[2] += 1

    tag = f"v{".".join(str(v) for v in version)}"

    if verify_tag(tag):
        utils.cmdx(f"git tag -d {tag}")
        utils.cmdx(f"git push origin --delete {tag}")

    utils.cmdx(f"git tag {tag}")
    utils.cmdx(f"git push origin {tag}")


def verify_tag(tag: str):
    result = utils.cmdx("git tag --list", print_out=False)
    return tag in result.split("\n")  # type: ignore


def main() -> None:
    """Main function"""

    publish()


if __name__ == "__main__":
    main()
