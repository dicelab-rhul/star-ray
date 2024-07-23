"""This module defines events base classes, such as `Event`, `Observation`, `Action` and various user input events."""

from .event import Event
from .user_event import (
    KeyEvent,
    MouseButtonEvent,
    MouseMotionEvent,
    JoyStickEvent,
    WindowFocusEvent,
    WindowMoveEvent,
    WindowResizeEvent,
    WindowCloseEvent,
    WindowOpenEvent,
    ScreenSizeEvent,
)
from .action_event import Action
from .observation_event import (
    Observation,
    ActiveObservation,
    ErrorActiveObservation,
    ErrorObservation,
    wrap_observation,
)

__all__ = (
    "Event",
    "Action",
    "Observation",
    "ActiveObservation",
    "ErrorActiveObservation",
    "ErrorObservation",
    # user input events
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
    # other
    "wrap_observation",
)
