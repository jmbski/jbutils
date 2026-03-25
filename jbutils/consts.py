"""Constant variables for the jbutils library"""

from typing import ClassVar

LOG_FMT_ID_CUSTOM = "[%(name)s::%(module)s::%(origFunc)s]"
LOG_FMT_ID = "[%(name)s::%(module)s::%(funcName)s"
LOG_FMT_RICH = f"{LOG_FMT_ID} %(message)s"
LOG_FMT_STND = f"%(asctime)s {LOG_FMT_ID} [%(levelname)s] %(message)s"
ROOT_LOG_HANDLERS = ["file", "console"]
LOG_HANDLERS = {
    "file_logger": ["file"],
}


class RuntimeGlobals:
    """Reference class for various global values to use at runtime"""

    debug: ClassVar[bool] = False
    """ Toggle to enable developer level debugging output """

    verbose: ClassVar[bool] = False
    """ Toggle to enable general level extra log output """

    use_rich_console: ClassVar[bool] = True
    """ Toggle this if you ever want to force-disable Rich console output. """

    log_fmt_std: ClassVar[str] = LOG_FMT_STND
    """ Log format for logging not using rich """

    log_fmt_rich: ClassVar[str] = LOG_FMT_RICH
    """ Log format for when using rich """

    root_log_handlers: ClassVar[list[str]] = ROOT_LOG_HANDLERS
    """ Default log handlers to use for the root logger """

    log_handler_map: ClassVar[dict[str, list]] = LOG_HANDLERS
    """ Mapping of logger names to handlers for non-root loggers """


__all__ = [
    "LOG_FMT_ID_CUSTOM",
    "LOG_FMT_ID",
    "LOG_FMT_RICH",
    "LOG_FMT_STND",
    "RuntimeGlobals",
]
