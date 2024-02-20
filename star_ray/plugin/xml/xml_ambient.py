from typing import List, Dict, Any
from .xml_state import XMLState
from .query_xpath import QueryXPath
from ...environment.ambient import Ambient
from ...event import ErrorResponse, UpdateResponse, SelectResponse


class XMLAmbient(Ambient):
    def __init__(self, agents: List[Any], xml: str, namespaces: Dict[str, str] = {}):
        super().__init__(agents)
        self.state = XMLState(xml, namespaces=namespaces)

    def __select__(self, query: QueryXPath) -> SelectResponse | ErrorResponse:
        return self.state.__select__(query)

    def __update__(self, query: QueryXPath) -> UpdateResponse | ErrorResponse:
        response = self.state.__update__(query)
        return response
