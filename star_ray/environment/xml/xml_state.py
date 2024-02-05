from lxml import etree as ET
from .query_xml import QueryXML
from .query_xpath import QueryXPath

from ...event import ResponseError


class XMLState:
    def __init__(self, xml, namespaces=None):
        super().__init__()
        self._root = ET.fromstring(xml)
        self._namespaces = dict() if namespaces is None else namespaces

    def __query__(self, query: QueryXPath):
        try:
            if isinstance(query, QueryXML):
                return QueryXML._query(self._root, query)
            elif isinstance(query, QueryXPath):
                return QueryXPath._query(self._root, query, namespaces=self._namespaces)
            else:
                raise ValueError(f"Unknown query type: {type(query)}.")
        except Exception as e:
            return ResponseError.new(query, e)
