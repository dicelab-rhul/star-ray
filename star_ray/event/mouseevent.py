""" Module defining the [MouseButtonEvent] and [MouseMotionEvent] classes. """

from typing import ClassVar
from dataclasses import dataclass, astuple
from .event import Event

__all__ = ("MouseButtonEvent", "MouseMotionEvent")


@dataclass
class MouseButtonEvent(Event):
    """
    A class representing a mouse event.

    Attributes:
        id ([str]): A unique identifier for the event, represented as a string (inherited).
        timestamp ([float]): The UNIX timestamp (in seconds) when the event instance is created (inherited).
        source ([str]): A unique identifier for the source of this event, represented as a string (inherited).
        button ([int]): The mouse button involved in the event (1 for left click, 2 for middle click, 3 for right click, etc.).
        position ([tuple]): The (x, y) coordinates of the mouse event.
        status ([int]): The status of the event (UP = 0, DOWN = 1, CLICK = 2).
        target ([str]): The UI element that was clicked on. This value is UI implementation dependent and may be None, typically it will be a unique element ID.
    """

    button: int
    position: tuple
    status: int
    target: str

    # static fields
    UP: ClassVar[int] = 0
    DOWN: ClassVar[int] = 1
    CLICK: ClassVar[int] = 2

    @staticmethod
    def new(
        source: str, button: int, position: tuple, status: int, target=None
    ) -> "MouseButtonEvent":
        return MouseButtonEvent(
            *astuple(Event.new(source)), button, position, status, target
        )

    @staticmethod
    def status_from_string(value: str) -> int:
        if "release" in value or value == "up":
            return MouseButtonEvent.UP
        elif "press" in value or value == "down":
            return MouseButtonEvent.DOWN
        elif "click" in value:
            return MouseButtonEvent.CLICK
        else:
            raise ValueError(
                f"Failed to convert status string: {value}, valid values include: ['released', 'pressed', 'clicked', 'up', 'down']"
            )


@dataclass
class MouseMotionEvent(Event):
    """
    A class representing a mouse motion event.

    Attributes:
        id ([str]): A unique identifier for the event, represented as a string (inherited).
        timestamp ([float]): The UNIX timestamp (in seconds) when the event instance is created (inherited).
        source ([str]): A unique identifier for the source of this event, represented as a string (inherited).
        position: ([tuple]): The window relative position of the mouse pointer.
        relative ([tuple]): The relative motion of the mouse since the last event.
        target ([str]): The UI element that the mouse is currently over. This value is UI implementation dependent and may be None, typically it will be a unique element ID.
    """

    position: tuple
    relative: tuple
    target: str

    @staticmethod
    def new(
        source: str, position: tuple, relative: tuple, target: str = None
    ) -> "MouseMotionEvent":
        return MouseMotionEvent(*astuple(Event.new(source)), position, relative, target)
