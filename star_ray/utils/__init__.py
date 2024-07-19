"""Package containing various useful utilities."""

from . import error
from ._async import _Future
from ._logging import _LOGGER
from ._uuid import int64_uuid, str_uuid4

from ._types import SliceType, EllipsisType
from ._templating import ValidatedTemplates, ValidatedEnvironment, TemplateLoader
from .type_routing import TypeRouter

__all__ = (
    "TypeRouter",
    "ValidatedTemplates",
    "ValidatedEnvironment",
    "TemplateLoader",
    "SliceType",
    "EllipsisType",
    "_Future",
    "error",
    "int64_uuid",
    "str_uuid4",
    "_LOGGER",
)
