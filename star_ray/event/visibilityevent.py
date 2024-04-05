""" Module defining the [VisibilityEvent] class. """

from typing import ClassVar
from pydantic import validator
from .event import Event


class VisibilityEvent(Event):
    """
    A class representing a visibility change event. If this event is triggered it is an indicator that the user has either:
        1. switch window (changed focus)
        2. switched tab (if using a browser based UI)
        3. minimised the UI window

    This event DOES NOT NECESSARILY indicate that the use cannot see the interface at all, this is due to inherent limitations with detecting visibility changes (e.g. in browser based UI's). See e.g. [visibilitychange](https://developer.mozilla.org/en-US/docs/Web/API/Document/visibilitychange_event)

      Attributes:
        id ([int]): A unique identifier for the event.
        timestamp ([float]): The timestamp (in seconds since UNIX epoch) when the event instance is created.
        source ([int]): A unique identifier for the source of this event.
        status ([int]): the visibility status (VISIBLE = 0, HIDDEN = 1).
    """

    status: int

    # static fields
    VISIBLE: ClassVar[int] = 0
    HIDDEN: ClassVar[int] = 1

    @validator("status")
    def _validate_status(cls, value: str | int):  # pylint: disable=E0213
        if isinstance(value, str):
            if "hidden" == value:
                return cls.HIDDEN
            elif "visible" == value:
                return cls.VISIBLE
            else:
                raise ValueError(
                    f"Failed to convert status string: {value}, valid values include: ['visible', 'hidden']"
                )
        elif isinstance(value, int) and value in [
            VisibilityEvent.VISIBLE,
            VisibilityEvent.HIDDEN,
        ]:
            return value
        else:
            raise ValueError(f"Invalid {type(VisibilityEvent)} status code: {value}")
