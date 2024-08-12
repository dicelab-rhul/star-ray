"""Module contains base classes for observations, see classes: `Observation`, `ActiveObservation`, `ErrorObservation`, `ErrorActiveObservation` documentation for details."""

import importlib
import traceback
from functools import lru_cache
from functools import wraps
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

    @staticmethod
    def new(action: Event, values: Any) -> "ActiveObservation":
        """Factory method.

        Args:
            action (Event): action that lead to this observation.
            values (Any): values that are part of this observation.

        Returns:
            ActiveObservation: the observation.
        """
        return ActiveObservation(action_id=action, values=values)


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

    exception_type: str  # fully qualified name of the exception type
    # list of arguments that came with the exception (these are retrieved via exception.__dict__)
    exception_args: dict[str, Any]  # TODO Any must be serializable...
    traceback_message: str  # traceback message of the exception

    def __str__(self):  # noqa: D105
        return f"ErrorResponse(\nsource={self.source},\n{self.traceback_message}\n)"

    def exception(self):
        """Creates an exception that may be re-raised, the exception contains information about the original error.

        Returns:
            _ObservationError: the exception to re-raise (or process)
        """
        return _ObservationError(f"\n{self.exception_type}:\n{self.traceback_message}")

    def resolve_exception_type(self) -> type:
        """Attempt to resolve the actual type of the exception that caused this error observation.

        Raises:
            TypeError: if the type could not be resolved.

        Returns:
            type: the exception type
        """
        etype = get_type_by_fully_qualified_name(self.exception_type)
        if etype is None:
            raise TypeError(f"Failed to resolve exception type: {self.exception_type}")
        else:
            return etype

    def from_exception(exception: Exception) -> "ErrorObservation":
        """Factory method that will build an instance from an `Exception`.

        Args:
            exception (Exception): the exception
        Returns:
            ErrorActiveObservation: the error observation
        """
        exception_type = get_fully_qualified_name(exception)
        traceback_message = "".join(
            traceback.format_exception(
                type(exception), value=exception, tb=exception.__traceback__
            )
        )
        return ErrorObservation(
            exception_type=exception_type,
            exception_args=exception.__dict__,  # TODO deepcopy?
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
        exception_type = get_fully_qualified_name(exception)
        traceback_message = "".join(
            traceback.format_exception(
                type(exception), value=exception, tb=exception.__traceback__
            )
        )
        return ErrorActiveObservation(
            action_id=action,
            exception_type=exception_type,
            exception_args=exception.__dict__,  # TODO deepcopy?
            traceback_message=traceback_message,
        )


class _ObservationError(Exception):
    """Wrapper exception class that will contain information about an exception that occured during observation computation."""


def wrap_observation(fun):
    """Decorator that will wrap the return value in an ActiveObservation or ErrorActiveObservation if there was an exception. Assumes that `action` is the first argument of the given function.

    Args:
        fun: function to decorate.
    """

    # TODO check that the first argument is an action!
    @wraps(fun)
    def _wrap(
        self, action: Event, *args, **kwargs
    ) -> ActiveObservation | ErrorActiveObservation:
        try:
            result = fun(self, action, *args, **kwargs)
            if not isinstance(result, ActiveObservation):
                return ActiveObservation.new(action, values=result)
            else:
                return result
        except Exception as e:
            return ErrorActiveObservation.from_exception(action, e)

    return _wrap


@lru_cache(maxsize=32)
def get_type_by_fully_qualified_name(fq_name: str) -> type | None:
    """Get type by its fully qualified name, uses `importlib` internally to do this. The result will be cached as this involves importing modules to locate the type."""
    module_name, type_name = fq_name.rsplit(".", 1)
    module = importlib.import_module(module_name)
    return getattr(module, type_name, None)


def get_fully_qualified_name(obj: Any) -> str:
    """Get the fully qualified name of a class from an instance of the class."""
    module = obj.__class__.__module__
    if module is None or module == str.__class__.__module__:
        return obj.__class__.__name__  # Built-in types
    return module + "." + obj.__class__.__name__
