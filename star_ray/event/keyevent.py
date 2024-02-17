""" Module defining the [KeyEvent] class. [KeyEvent] is used to represent user keyboard input."""

from dataclasses import dataclass
from .event import Event
from typing import ClassVar


@dataclass
class KeyEvent(Event):
    """A class representing a keyboard event.

    Attributes:
        id ([str]): A unique identifier for the event, represented as a [string (inherited).
        timestamp ([float]): The UNIX timestamp (in seconds) when the event instance is created (inherited).
        source ([str]): A unique identifier for the source of this event, represented as a string (inherited).

        key ([int]): The key code of the keyboard event.
        key_name ([str]): The name of the key pressed or released.
        status ([int]): The status of the key event (PRESS = 0, RELEASE = 1, HOLD = 2).

    Static Attributes:

    """

    key: int
    key_name: str
    status: int

    PRESS: ClassVar[int] = 0
    RELEASE: ClassVar[int] = 1
    HOLD: ClassVar[int] = 2
