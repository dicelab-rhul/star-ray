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

    def __init__(self, exception: Exception = None, **kwargs):
        assert exception
        exception_type = exception.__class__.__name__
        traceback_message = "".join(
            traceback.format_exception(
                type(exception), value=exception, tb=exception.__traceback__
            )
        )
        super().__init__(
            exception_type=exception_type, traceback_message=traceback_message, **kwargs
        )

    def __str__(self):
        return f"ErrorResponse(\nsource={self.source},\n{self.traceback_message}\n)"

    def exception(self):
        return _ObservationError(f"\n{self.exception_type}:\n{self.traceback_message}")


class ErrorActiveObservation(ActiveObservation, ErrorObservation):
    pass


class _ObservationError(Exception):
    pass
