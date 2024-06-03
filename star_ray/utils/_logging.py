import logging
from functools import wraps

# NOTE: _LOGGER is deprecated use LOGGER
__all__ = ("_LOGGER", "LOGGER", "Indent")

LOGGER = logging.getLogger(__package__)


class Indent:

    def __init__(self, spaces=2):
        self.logging_indent_level = 0
        self.logging_indent_spaces = " " * spaces

    def __call__(self, fun):
        @wraps(fun)
        def _log_with_indent(*args, **kwargs):
            with self:
                return fun(*args, **kwargs)

        return _log_with_indent

    def __enter__(self):
        self.logging_indent_level = self.logging_indent_level + 1
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.logging_indent_level = self.get_current_indent_level() - 1

    def get_current_indent_level(self):
        return self.logging_indent_level

    def get_current_ident(self):
        return self.logging_indent_level * self.logging_indent_spaces


class IndentFormatter(logging.Formatter):

    def format(self, record):
        if not hasattr(record, "indent"):
            setattr(record, "indent", LOGGER.indent.get_current_ident())
        return super().format(record)


LOGGER.setLevel(logging.DEBUG)
handler = logging.StreamHandler()
handler.setLevel(logging.DEBUG)
formatter = IndentFormatter("%(levelname)s: %(indent)s%(message)s")
handler.setFormatter(formatter)
LOGGER.addHandler(handler)


def format_iterable(iterable, message, join="\n", indent=True):
    if indent:
        ind = "  " * LOGGER.indent.get_current_indent_level()
    else:
        ind = ""
    return join.join([f"{ind}{message}{x}" for x in iterable])


LOGGER.format_iterable = format_iterable
LOGGER.indent = Indent()
_LOGGER = LOGGER  # TODO _LOGGER is deprecated, it will be removed soon
