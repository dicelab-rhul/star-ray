import traceback
from typing import Dict, List, Any
from pydantic import validator
from .event import Event


class Response(Event):
    # this is the source of the query
    query_id: int

    @validator("query_id", pre=True, always=True)
    def _validate_query_id(cls, value):  # pylint: disable=E0213
        if isinstance(value, Event):
            return value.id
        elif isinstance(value, int):
            return value
        else:
            raise ValueError(f"Invalid query_id {value}")


class SelectResponse(Response):
    values: List[Any] | Dict[str, Any]

    def __init__(self, query: Event | int, values: List[Any] | Dict[str, Any]):
        super().__init__(query_id=query, values=values)


class UpdateResponse(Response):

    def __init__(self, query: Event | int):
        super().__init__(query_id=query)


class ErrorResponse(Response):
    exception_type: str
    traceback_message: str

    def __init__(self, query: Event | int, exception: Exception):
        exception_type = exception.__class__.__name__
        traceback_message = "\n".join(
            traceback.format_exception(
                type(exception), value=exception, tb=exception.__traceback__
            )
        )
        super().__init__(
            query_id=query,
            exception_type=exception_type,
            traceback_message=traceback_message,
        )

    def __str__(self):
        return f"ErrorResponse(\nsource={self.source},\n{self.traceback_message}\n)"
