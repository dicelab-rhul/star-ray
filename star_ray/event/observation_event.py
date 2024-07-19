"""Module contains base classes for observations, see classes: `Observation`, `ActiveObservation`, `ErrorObservation`, `ErrorActiveObservation` documentation for details."""

import traceback
from typing import Any
from pydantic import field_validator, Field
from .event import Event


class Observation(Event):
    """Base class for an observation. Contains `values` (any type) which holds the observed data."""

    values: Any = Field(default_factory=lambda: None)


class ActiveObservation(Observation):
    """Base class for an observation that was the result of an action. Contains `action_id` which is the unique `id` of the action that generated this observation."""

    action_id: int

    @field_validator("action_id", mode="before")
    def _validate_query_id(cls, value):
        if isinstance(value, Event):
            return value.id
        elif isinstance(value, int):
            return value
        else:
            raise ValueError(f"Invalid action_id {value}")


class ErrorObservation(Observation):
    """Base class for an observation that contains an error.

    This typically means an exception was raised during some computation that is related to the observation. It holds relevant exception information, the exception can be re-raised using: `raise observation.exception()`.

    The factory method `from_exception` is the easiest way to create this kind of observation in a try-catch block.
    ```
    try:
        ...
    catch Exception as e:
        return ErrorObservation.from_exception(e)
    ```
    """

    exception_type: str
    traceback_message: str

    def __str__(self):  # noqa: D105
        return f"ErrorResponse(\nsource={self.source},\n{self.traceback_message}\n)"

    def exception(self):
        """Creates an exception that may be re-raised, the exception contains information about the original error.

        Returns:
            _ObservationError: the exception to re-raise (or process)
        """
        return _ObservationError(f"\n{self.exception_type}:\n{self.traceback_message}")

    def from_exception(exception: Exception) -> "ErrorObservation":
        """Factory method that will build an instance from an `Exception`.

        Args:
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
        return ErrorObservation(
            exception_type=exception_type,
            traceback_message=traceback_message,
        )


class ErrorActiveObservation(ErrorObservation, ActiveObservation):
    """An observation that contains an error and was the result of an action."""

    def from_exception(action: Event, exception: Exception) -> "ErrorActiveObservation":
        """Factory for `ErrorActiveObservation` that will build an instance from an `Exception`.

        Args:
            action (Event): the action that led to the exception
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
            action_id=action,
            exception_type=exception_type,
            traceback_message=traceback_message,
        )


class _ObservationError(Exception):
    """Wrapper exception class that will contain information about an exception that occured during observation computation."""
