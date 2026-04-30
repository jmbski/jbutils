"""Common types shared among FastAPI implementations"""

import logging

from collections.abc import Callable
from typing import Annotated, Any

from fastapi import Depends, Request


def get_logger(name: str = "gunicorn.error") -> logging.Logger:
    return logging.getLogger(name)


# (request: Request, call_next, logger: ApiLogger):
ApiLogger = Annotated[logging.Logger, Depends(get_logger)]
ApiHttpCallback = Callable[[Request, Any], Any]
