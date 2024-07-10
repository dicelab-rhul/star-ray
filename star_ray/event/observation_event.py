import traceback
from typing import Dict, List, Any
from pydantic import validator, Field
from .event import Event


class Observation(Event):
    values: Any = Field(default_factory=lambda: None)


class ActiveObservation(Observation):
    action_id: int

    @validator("action_id", pre=True, always=True)
    def _validate_query_id(cls, value):  # pylint: disable=E0213
        if isinstance(value, Event):
            return value.id
        elif isinstance(value, int):
            return value
        else:
            raise ValueError(f"Invalid action_id {value}")


class ErrorObservation(Observation):
    exception_type: str
    traceback_message: str

    def __str__(self):
        return f"ErrorResponse(\nsource={self.source},\n{self.traceback_message}\n)"

    def exception(self):
        return _ObservationError(f"\n{self.exception_type}:\n{self.traceback_message}")

    def from_exception(action: Event | int, exception: Exception, **kwargs) -> "ErrorActiveObservation":
        """Factory for `ErrorActiveObservation` that will build an instance from an `Exception`.

        Args:
            action (Event | int): the action that caused the exception (or it's unique `id`).
            exception (Exception): the exception

        Returns:
            ErrorActiveObservation: the error observation
        """
        exception_type = exception.__class__.__name__
        traceback_message = "".join(
            traceback.format_exception(
                type(exception), value=exception, tb=exception.__traceback__
            )
        )
        return ErrorActiveObservation(
            action_id=action, exception_type=exception_type, traceback_message=traceback_message, **kwargs
        )


class ErrorActiveObservation(ErrorObservation, ActiveObservation):
    pass


class _ObservationError(Exception):
    pass
