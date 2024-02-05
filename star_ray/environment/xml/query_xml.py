from dataclasses import dataclass, astuple
from typing import List, Dict, Any
from lxml import etree as ET

from .query_xpath import QueryXPath
from ._utils import _tostring, _xml_to_primitive
from ...event import Response


@dataclass
class QueryXML(QueryXPath):
    element_id: str

    @staticmethod
    def new(element_id: str, attributes: List[str] | Dict[str, Any]) -> "QueryXML":
        assert isinstance(attributes, (list, dict))
        xpath = f"//*[@id='%s']"
        return QueryXML(*astuple(QueryXPath.new(xpath, attributes)), element_id)

    @staticmethod
    def _xpath(root: ET._Element, xpath: str):
        elements = root.xpath(xpath)
        if len(elements) == 0:
            raise ValueError(f"No element was found with xml query: {xpath}")
        if len(elements) > 1:
            raise ValueError(
                f"More than one element was found with xml query {xpath}, '@id' should be a unique identifier"
            )
        return elements[0]

    @staticmethod
    def _query(root: ET._Element, query: "QueryXML") -> "Response":
        if isinstance(query.attributes, list):
            return QueryXML._select(root, query)
        elif isinstance(query.attributes, dict):
            return QueryXML._update(root, query)
        else:
            raise ValueError(
                f"Invalid type {type(query.attributes)} for query attributes."
            )

    @staticmethod
    def _select(root: ET._Element, query: "QueryXML"):
        xpath = query.xpath % query.element_id
        element = QueryXML._xpath(root, xpath)

        if len(query.attributes) > 0:
            result = {}
            for key in query.attributes:
                # TODO re raise the exception?
                result[key] = _xml_to_primitive(element.get(key))
            result = {query.element_id: result}
        else:
            # select the element itself
            result = {query.element_id: _tostring(element)}
        return Response.new(query, True, result)

    @staticmethod
    def _update(root: ET._Element, query: "QueryXML"):
        xpath = query.xpath % query.element_id
        element = QueryXML._xpath(root, xpath)
        result = {}
        # TODO if attributes is a str then update the element itself?
        for key, value in query.attributes.items():
            # TODO re raise the exception?
            result[key] = _xml_to_primitive(element.get(key))
            element.set(key, str(value))
        result = {query.element_id: result}
        return Response.new(query, True, result)
