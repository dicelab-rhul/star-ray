from dataclasses import dataclass, astuple, field
import traceback
from typing import Dict, List, Any, Optional

from ..event import Event


@dataclass
class Response(Event):
    query_id: str
    success: bool

    @staticmethod
    def new(
        source: str,
        query: Event,
        success: bool,
    ):
        return Response(*astuple(Event.new(source)), query.id, success)


@dataclass
class ResponseSelect(Response):
    values: List[Any] | Dict[str, Any]

    @staticmethod
    def new(source: str, query: Event, success: bool, data: List[Any] | Dict[str, Any]):
        return ResponseSelect(*astuple(Event.new(source)), query.id, success, data)


@dataclass
class ResponseUpdate(Response):
    # new_values: Optional[Dict[str, Any]] = field(default=None)
    # old_values: Optional[Dict[str, Any]] = field(default=None)

    @staticmethod
    def new(
        source: str,
        query: Event,
        success: bool,
        # new_values: Optional[Dict[str, Any]] = None,
        # old_values: Optional[Dict[str, Any]] = None,
    ):
        return ResponseUpdate(
            *astuple(Event.new(source)), query.id, success  # , new_values, old_values
        )


@dataclass
class ResponseError(Response):
    exception_type: str
    error_message: str
    stack_trace: str

    @staticmethod
    def new(source: str, query: Event, success: bool, exception: Exception):
        exception_type = exception.__class__.__name__
        error_message = str(exception)
        stack_trace = "".join(
            traceback.format_exception(
                type(exception), value=exception, tb=exception.__traceback__
            )
        )
        return ResponseError(
            *astuple(Event.new(source)),
            query.id,
            success,
            exception_type,
            error_message,
            stack_trace,
        )
