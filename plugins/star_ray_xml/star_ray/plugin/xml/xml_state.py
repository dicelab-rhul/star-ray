""" TODO """

from typing import Dict
from lxml import etree as ET
from star_ray.event import ActiveObservation, ErrorActiveObservation

from .query_xpath import QueryXPath


class XMLState:
    """
    A class to represent and manipulate XML state data.

    This class provides a structured way to interact with XML data using XPath queries (see `XPathQuery`) for selection and updates. It supports namespace definitions to handle XML data that includes namespaces.

    Methods:
        __select__(query: QueryXPath): Executes a read XPath query on the XML data.
        __update__(query: QueryXPath): Executes a write XPath query on the XML data.

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

    def __select__(
        self, query: QueryXPath
    ) -> ActiveObservation | ErrorActiveObservation:
        try:
            # TODO handle source attribute on observation?
            return query.__select__(self._root, namespaces=self._namespaces)
        except Exception as e:
            return ErrorActiveObservation(action_id=query, exception=e)

    def __update__(
        self, query: QueryXPath
    ) -> ActiveObservation | ErrorActiveObservation:
        try:
            # TODO handle source attribute on observation?
            return query.__update__(
                self._root,
                namespaces=self._namespaces,
                parser=self._parser,
            )
        except Exception as e:
            return ErrorActiveObservation(action_id=query, exception=e)
