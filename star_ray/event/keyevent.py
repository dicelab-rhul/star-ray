""" Module defining the [KeyEvent] class. [KeyEvent] is used to represent user keyboard input."""

from typing import ClassVar, Union
from pydantic import validator
from .event import Event


class KeyEvent(Event):
    """A class representing a keyboard event.

    Attributes:
        id ([int]): A unique identifier for the event.
        timestamp ([float]): The timestamp (in seconds since UNIX epoch) when the event instance is created.
        source ([int]): A unique identifier for the source of this event.
        key ([str]): The string representation of the key.
        keyCode ([int]): The key code of the keyboard event.
        status ([int]): The status of the key event (UP = 0, DOWN = 1, HOLD = 2).
    """

    key: str
    keyCode: int
    status: int

    UP: ClassVar[int] = 0
    DOWN: ClassVar[int] = 1
    HOLD: ClassVar[int] = 2

    @validator("status")
    def _validate_status(cls, value: Union[str, int]):  # pylint: disable=E0213
        if isinstance(value, str):
            if "release" in value or value == "up":
                return cls.UP
            elif "press" in value or value == "down":
                return cls.DOWN
            elif "hold" in value:
                return cls.HOLD
            else:
                raise ValueError(
                    f"Failed to convert status string: {value}, valid values include: ['released', 'pressed', 'clicked', 'up', 'down']"
                )
        elif isinstance(value, int) and value in [
            KeyEvent.UP,
            KeyEvent.DOWN,
            KeyEvent.HOLD,
        ]:
            return value
        else:
            raise ValueError(f"Invalid {type(KeyEvent)} status code: {value}")
