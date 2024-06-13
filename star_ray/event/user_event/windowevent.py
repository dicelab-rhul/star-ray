from typing import Tuple
from ..event import Event


class WindowMoveEvent(Event):
    position: Tuple[int, int] | Tuple[float, float]


class WindowResizeEvent(Event):
    size: Tuple[int, int] | Tuple[float, float]


class WindowCloseEvent(Event):
    pass


class WindowOpenEvent(Event):
    pass


class WindowFocusEvent(Event):
    has_focus: bool
