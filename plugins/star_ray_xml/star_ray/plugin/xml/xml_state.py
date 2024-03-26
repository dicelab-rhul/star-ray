""" TODO """

from typing import Dict
from lxml import etree as ET
from star_ray.event import ErrorResponse, SelectResponse, UpdateResponse

from .query_xpath import QueryXPath


class XMLState:
    """
    A class to represent and manipulate XML state data.

    This class provides a structured way to interact with XML data using XPath queries (see `XPathQuery`) for selection and updates. It supports namespace definitions to handle XML data that includes namespaces.

    Methods:
        __select__(query: QueryXPath) -> ResponseSelect | ResponseError: Executes a read-only XPath query on the XML data and returns a `ResponseSelect` object for successful queries or a `ResponseError` object in case of an error.
        __update__(query: QueryXPath) -> ResponseUpdate | ResponseError: Executes a write XPath query on the XML data and returns a `ResponseUpdate` object for successful updates or a `ResponseError` object in case of an error.

    The `__select__` method is designed to be safe for parallel execution, allowing for efficient read operations on the XML data.
    The `__update__` method handles write operations and modifies the XML state.
    """

    def __init__(
        self, xml: str, namespaces: Dict[str, str] = None, parser: ET.XMLParser = None
    ):
        super().__init__()
        if parser is None:
            parser = ET.XMLParser()
        self._parser = parser
        self._root = ET.fromstring(xml, parser=self._parser)  # pylint: disable=I1101
        self._namespaces = dict() if namespaces is None else namespaces

    def __select__(self, query: QueryXPath) -> SelectResponse | ErrorResponse:
        # TODO this is a read only query and can be executed in parallel
        try:
            return query.__select__(
                "environment", self._root, namespaces=self._namespaces
            )
        except Exception as e:
            return ErrorResponse.new("environment", query, e)

    def __update__(self, query: QueryXPath) -> UpdateResponse | ErrorResponse:
        # TODO this is a write query
        try:
            return query.__update__(
                "environment",
                self._root,
                namespaces=self._namespaces,
                parser=self._parser,
            )
        except Exception as e:
            return ErrorResponse.new("environment", query, e)
