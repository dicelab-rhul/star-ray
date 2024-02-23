# from .logging import LOGGER, info, debug, warning, error, exception

# _
# _all__ = ("LOGGER", "info", "debug", "warning", "error", "exception")

from . import error
from ._utils import new_uuid

__all__ = (
    "error",
    "new_uuid",
)
