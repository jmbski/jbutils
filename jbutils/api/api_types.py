"""Common types shared among FastAPI implementations"""

import logging

from collections.abc import Callable
from typing import Annotated, Any

from fastapi import Depends, Request

from jbutils.api import api_utils

# (request: Request, call_next, logger: ApiLogger):
ApiLogger = Annotated[logging.Logger, Depends(api_utils.get_logger)]
ApiHttpCallback = Callable[[Request, Any, ApiLogger], Any]
