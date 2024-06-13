""" Module defining the `MouseButtonEvent` and `MouseMotionEvent` classes. """

from typing import ClassVar, Tuple, List
from pydantic import validator, Field
from ..event import Event

__all__ = ("MouseButtonEvent", "MouseMotionEvent")


class MouseButtonEvent(Event):
    """
    A class representing a mouse event.

    Attributes:
        id ([int]): A unique identifier for the event.
        timestamp ([float]): The timestamp (in seconds since UNIX epoch) when the event instance is created.
        source ([int]): A unique identifier for the source of this event.
        button ([int]): The mouse button involved in the event (1 for left click, 2 for middle click, 3 for right click, etc.).
        position ([tuple]): The (x, y) coordinates of the mouse event.
        status ([int]): The status of the event (UP = 0, DOWN = 1, CLICK = 2).
        target ([str]): The UI element that was clicked on. This value is UI implementation dependent and may be None, typically it will be a unique element ID.
    """

    button: int
    position: Tuple[float, float] | Tuple[int, int]
    status: int
    target: str | List[str] | None = Field(default=None)

    # static fields
    UP: ClassVar[int] = 0
    DOWN: ClassVar[int] = 1
    CLICK: ClassVar[int] = 2

    BUTTON_LEFT: ClassVar[int] = 0
    BUTTON_MIDDLE: ClassVar[int] = 1
    BUTTON_RIGHT: ClassVar[int] = 2

    @validator("position", pre=True, always=True)
    @classmethod
    def _validate_position(cls, value: tuple | dict | list):
        if isinstance(value, dict):
            return (value["x"], value["y"])
        else:
            return tuple(value)

    @validator("status", pre=True, always=True)
    @classmethod
    def _validate_status(cls, value: str | int) -> int:  # pylint: disable=E0213
        if isinstance(value, str):
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
        elif isinstance(value, int) and value in [
            MouseButtonEvent.UP,
            MouseButtonEvent.DOWN,
            MouseButtonEvent.CLICK,
        ]:
            return value
        else:
            raise ValueError(f"Invalid {type(MouseButtonEvent)} status code: {value}")


class MouseMotionEvent(Event):
    """
    A class representing a mouse motion event.

    Attributes:
        id ([int]): A unique identifier for the event.
        timestamp ([float]): The timestamp (in seconds since UNIX epoch) when the event instance is created.
        source ([int]): A unique identifier for the source of this event.
        position: ([Tuple[float,float]]): The window relative position of the mouse pointer.
        relative ([Tuple[float,float]]): The relative motion of the mouse since the last event.
        target ([str | List[str]]): The UI element that the mouse is currently over. This value is UI implementation dependent and may be None, typically it will be a unique element ID.
    """

    position: Tuple[float, float] | Tuple[int, int]
    relative: Tuple[float, float] | Tuple[int, int]
    target: str | List[str] | None = Field(default=None)
