from typing import List, Dict, Any
from .xml_state import XMLState
from .event_xpath import QueryXPath
from ...environment.ambient import Ambient
from ...event import ResponseError, ResponseUpdate, ResponseSelect


class XMLAmbient(Ambient):
    def __init__(self, agents: List[Any], xml: str, namespaces: Dict[str, str] = {}):
        super().__init__(agents)
        self.state = XMLState(xml, namespaces=namespaces)

    def __select__(self, query: QueryXPath) -> ResponseSelect | ResponseError:
        return self.state.__select__(query)

    def __update__(self, query: QueryXPath) -> ResponseUpdate | ResponseError:
        response = self.state.__update__(query)
        return response
