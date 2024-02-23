import traceback


from dataclasses import dataclass, astuple, field
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
class SelectResponse(Response):
    values: List[Any] | Dict[str, Any]

    @staticmethod
    def new(
        source: str, query: Event | str, success: bool, data: List[Any] | Dict[str, Any]
    ):
        if isinstance(query, Event):
            query = query.id
        return SelectResponse(*astuple(Event.new(source)), query, success, data)


@dataclass
class UpdateResponse(Response):
    # new_values: Optional[Dict[str, Any]] = field(default=None)
    # old_values: Optional[Dict[str, Any]] = field(default=None)

    @staticmethod
    def new(
        source: str,
        query: Event | str,
        success: bool,
        # new_values: Optional[Dict[str, Any]] = None,
        # old_values: Optional[Dict[str, Any]] = None,
    ):
        if isinstance(query, Event):
            query = query.id
        return UpdateResponse(
            *astuple(Event.new(source)), query, success  # , new_values, old_values
        )


@dataclass
class ErrorResponse(Response):
    exception_type: str
    error_message: str
    stack_trace: str

    @staticmethod
    def new(source: str, query: Event, exception: Exception):
        exception_type = exception.__class__.__name__
        error_message = str(exception)
        stack_trace = "".join(
            traceback.format_exception(
                type(exception), value=exception, tb=exception.__traceback__
            )
        )
        return ErrorResponse(
            *astuple(Event.new(source)),
            query.id,
            False,
            exception_type,
            error_message,
            stack_trace,
        )

    def __str__(self):
        # TODO update this maybe? include all fields?
        return f"ErrorResponse(\nsource={self.source},\nexception_type={self.exception_type},\nerror_message={self.error_message},\nstack_trace=\n{self.stack_trace})"
