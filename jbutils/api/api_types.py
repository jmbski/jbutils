"""Common types shared among FastAPI implementations"""

import logging

from typing import Annotated

from fastapi import Depends

from jbutils.api import api_utils

ApiLogger = Annotated[logging.Logger, Depends(api_utils.get_logger)]
