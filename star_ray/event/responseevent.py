from dataclasses import dataclass, astuple
from ..event import Event
from typing import Dict, List, Any


@dataclass
class Response(Event):
    query_id: str
    success: bool
    data: List[Any] | Dict[str, Any]

    @staticmethod
    def new(query: Event, success: bool, data: List[Any] | Dict[str, Any]):
        return Response(*astuple(Event.new()), query.id, success, data)


@dataclass
class ResponseError(Response):
    error: Exception

    @staticmethod
    def new(query: Event, error: Exception):
        return ResponseError(*astuple(Response.new(query, False, {})), error)
