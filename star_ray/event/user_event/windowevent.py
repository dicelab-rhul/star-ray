"""Module contains events related to application window changes.

Typically there will only be one such window as part of a simulation and so no details of the window (e.g. title) are provided. If this is required, extend the classes present here.
"""

from ..event import Event


class WindowMoveEvent(Event):
    """Event indicating that an application window was moved."""

    position: tuple[int, int] | tuple[float, float]


class WindowResizeEvent(Event):
    """Event indicating that an application window was resized."""

    size: tuple[int, int] | tuple[float, float]


class WindowCloseEvent(Event):
    """Event indicating that an application window was closed."""

    pass


class WindowOpenEvent(Event):
    """Event indicating that an application window was opened."""

    pass


class WindowFocusEvent(Event):
    """Event representing a change in an application window focus."""

    has_focus: bool


class ScreenSizeEvent(Event):
    """Event indicating that the screen/monitor has a given size."""

    size: tuple[float, float] | tuple[int, int]
