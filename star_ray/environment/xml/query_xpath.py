from dataclasses import dataclass, astuple
from typing import List, Dict, Any
from lxml import etree as ET

from ...event import Response, Event
from ._utils import _tostring, _xml_to_primitive


@dataclass
class QueryXPath(Event):
    xpath: str
    attributes: List[str] | Dict[str, Any] | str

    @staticmethod
    def new(xpath: str, attributes: List[str] | Dict[str, Any] | str):
        return QueryXPath(*astuple(Event.new()), xpath, attributes)

    @staticmethod
    def new_select(xpath: str, attributes: List[str] = []):
        return QueryXPath(*astuple(Event.new()), xpath, attributes)

    @staticmethod
    def new_update(xpath: str, attributes: Dict[str, Any] | str):
        return QueryXPath(*astuple(Event.new()), xpath, attributes)

    @staticmethod
    def _query(root: ET._Element, query: "QueryXPath", namespaces: Dict[str, str] = {}):
        if isinstance(query.attributes, list):
            return QueryXPath._select(root, query, namespaces=namespaces)
        elif isinstance(query.attributes, dict | str):
            return QueryXPath._update(root, query, namespaces=namespaces)
        else:
            raise ValueError(
                f"Invalid type {type(query.attributes)} for query attributes."
            )

    @staticmethod
    def _select(
        root: ET._Element, query: "QueryXPath", namespaces: Dict[str, str] = dict()
    ):
        # gather elements from xpath query
        elements = root.xpath(query.xpath, namespaces=namespaces)
        results = [_select_element(query, element) for element in elements]
        return Response.new(query, success=True, data=results)

    @staticmethod
    def _update(
        root: ET._Element, query: "QueryXPath", namespaces: Dict[str, str] = {}
    ):
        # gather elements from xpath query
        elements = root.xpath(query.xpath, namespaces=namespaces)
        results = [
            _update_element(query, element, namespaces=namespaces)
            for element in elements
        ]
        return Response.new(query, success=True, data=results)


def _update_element(query: QueryXPath, element: Any, namespaces: Dict[str, str] = {}):
    if isinstance(element, ET._Element):
        if isinstance(query.attributes, dict):
            assert len(query.attributes) > 0
            # TODO rather than none, return a Missing object?
            result = {
                attrib: _xml_to_primitive(element.get(attrib, None))
                for attrib in query.attributes
            }
            for attrib, value in query.attributes.items():
                element.set(attrib, str(value))
            return result
        elif isinstance(query.attributes, str):
            # we are updating the element itself
            parent = element.getparent()
            result = _tostring(element)
            # this dummy root node allows namespacing to be handled correctly
            namespaced_xml = f"""<_dummy { ' '.join(f'xmlns:{k}="{v}"' for k,v in namespaces.items())}> {query.attributes} </_dummy>"""
            namespaced_xml_node = next(iter(ET.fromstring(namespaced_xml)))
            parent.replace(element, namespaced_xml_node)
            return result
    elif isinstance(element, ET._ElementUnicodeResult):
        if not isinstance(query.attributes, str):
            raise ValueError(
                f"Invalid query 'attributes' type: {type(query.attributes)} for direct attribute/text update, must be of type {str}"
            )
        return _update_unicode_result(query, element)
    else:
        raise ValueError(f"Unknown element type {type(element)}.")


def _update_unicode_result(query: QueryXPath, element: ET._ElementUnicodeResult):
    parent = element.getparent()
    if element.is_text:
        parent.text = str(query.attributes)
        return str(element)
    elif element.is_attribute:
        parent.set(element.attrname, str(query.attributes))
        return {element.attrname: _xml_to_primitive(str(element))}
    else:
        raise ValueError(
            f"Unknown element: {element}, failed to update with query {query}."
        )


def _select_element(query: QueryXPath, element: Any):
    if isinstance(element, ET._Element):
        if len(query.attributes) > 0:
            # TODO rather than none, return a Missing object?
            return {
                attrib: _xml_to_primitive(element.get(attrib, None))
                for attrib in query.attributes
            }
        else:
            # return the XML element itself!
            return _tostring(element)
    elif isinstance(element, ET._ElementUnicodeResult):
        if element.is_attribute:
            return {element.attrname: _xml_to_primitive(str(element))}
        else:
            return str(element)
    else:
        raise ValueError(f"Unknown element type {type(element)}.")
