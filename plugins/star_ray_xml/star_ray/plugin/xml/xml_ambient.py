from typing import List, Dict, Any
from lxml import etree
from star_ray.environment.ambient import Ambient
from star_ray.event import ErrorResponse, UpdateResponse, SelectResponse

from .xml_state import XMLState
from .query_xpath import QueryXPath


class XMLAmbient(Ambient):
    def __init__(
        self,
        agents: List[Any],
        xml: str,
        namespaces: Dict[str, str] = {},
        parser: etree.XMLParser = None,
    ):
        super().__init__(agents)
        if parser is None:
            parser = etree.XMLParser()
        self.state = XMLState(xml, namespaces=namespaces, parser=parser)

    def __select__(self, query: QueryXPath) -> SelectResponse | ErrorResponse:
        return self.state.__select__(query)

    def __update__(self, query: QueryXPath) -> UpdateResponse | ErrorResponse:
        response = self.state.__update__(query)
        return response
