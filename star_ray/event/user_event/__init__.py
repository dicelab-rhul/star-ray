"""Package defining common user input events."""

from .keyevent import KeyEvent
from .mouseevent import MouseButtonEvent, MouseMotionEvent
from .joystickevent import JoyStickEvent
from .windowevent import (
    WindowFocusEvent,
    WindowMoveEvent,
    WindowResizeEvent,
    WindowCloseEvent,
    WindowOpenEvent,
    ScreenSizeEvent,
)

__all__ = (
    "KeyEvent",
    "JoyStickEvent",
    "MouseButtonEvent",
    "MouseMotionEvent",
    "WindowFocusEvent",
    "WindowMoveEvent",
    "WindowResizeEvent",
    "WindowCloseEvent",
    "WindowOpenEvent",
    "ScreenSizeEvent",
)
