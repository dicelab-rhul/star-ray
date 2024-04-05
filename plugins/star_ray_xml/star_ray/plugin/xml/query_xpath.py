# pylint: disable=[I1101,W0212,W0221]


from dataclasses import dataclass, astuple
from typing import List, Dict, Any
from lxml import etree as ET

from star_ray.event import SelectResponse, UpdateResponse, ErrorResponse, Event
from ._utils import _tostring, _xml_to_primitive


@dataclass
class QueryXPath(Event):
    xpath: str
    attributes: List[str] | Dict[str, Any] | str

    @staticmethod
    def new(source: str, xpath: str, attributes: List[str] | Dict[str, Any] | str):
        return QueryXPath(*astuple(Event.new(source)), xpath, attributes)

    def __select__(
        self,
        source: str,
        root: ET._Element,
        namespaces: Dict[str, str] = None,
        **kwargs,
    ) -> SelectResponse | ErrorResponse:
        if isinstance(self.attributes, list):
            results = _select(self.xpath, self.attributes, root, namespaces=namespaces)
            return SelectResponse.new(source, self, success=True, data=results)
        else:
            raise TypeError(
                f"Invalid type {type(self.attributes)} for SELECT query attributes."
            )

    def __update__(
        self,
        source: str,
        root: ET._Element,
        namespaces: Dict[str, str] = None,
        parser: ET.XMLParser = None,
        **kwargs,
    ) -> UpdateResponse | ErrorResponse:
        if isinstance(self.attributes, dict | str):
            return _update(source, root, self, namespaces=namespaces, parser=parser)
        else:
            raise ValueError(
                f"Invalid type {type(self.attributes)} for update query attributes."
            )


def _select(
    xpath: str,
    attributes: List[str],
    root: ET._Element,
    namespaces: Dict[str, str] = None,
):
    elements = root.xpath(xpath, namespaces=namespaces)
    print("----", xpath, elements)

    # TODO some xpath queries do not return a list of elements, they may return a value (e.g. a float from `count()`)
    if isinstance(elements, (int, float, bool, str)):
        return elements
    elif isinstance(elements, (ET._Element, ET._ElementUnicodeResult)):
        return _select_element(attributes, elements)
    else:
        return [_select_element(attributes, element) for element in elements]


def _select_element(attributes: List[str], element: Any):

    if isinstance(element, ET._Element):
        if len(attributes) > 0:
            # TODO rather than none, return a Missing object?
            return {
                attrib: _xml_to_primitive(element.get(attrib, None))
                for attrib in attributes
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


def _update(
    source: str,
    root: ET._Element,
    query: "QueryXPath",
    namespaces: Dict[str, str] = None,
    parser: ET.XMLParser = None,
    return_old_values: bool = False,
    return_new_values: bool = False,
):
    # gather elements from xpath query
    elements = root.xpath(query.xpath, namespaces=namespaces)
    # TODO updating multiple elements when there is an error may break the on_change... the response will not reflect the actual changes made?
    _ = [
        _update_element(query.attributes, element, namespaces=namespaces, parser=parser)
        for element in elements
    ]
    return UpdateResponse.new(source, query, success=True)


def _update_element(
    attributes: Dict[str, Any],
    element: Any,
    namespaces: Dict[str, str] = None,
    parser: ET.XMLParser = None,
    return_old_values: bool = False,
    return_new_values: bool = False,
):
    if isinstance(element, ET._Element):
        if isinstance(attributes, dict):
            assert len(attributes) > 0
            # TODO rather than none, return a Missing object?
            # result = {
            #     attrib: _xml_to_primitive(element.get(attrib, None))
            #     for attrib in attributes
            # }
            for attrib, value in attributes.items():
                # TODO raise a warning if the attribute doesnt exist? what to do here...
                element.set(attrib, str(value))
            # return result
        elif isinstance(attributes, str):
            # we are updating the element itself
            parent = element.getparent()
            # result = _tostring(element)
            # this dummy root node allows namespacing to be handled correctly
            namespaced_xml = f"""<_dummy { ' '.join(f'xmlns:{k}="{v}"' for k,v in namespaces.items())}> {attributes} </_dummy>"""
            namespaced_xml_node = next(
                iter(ET.fromstring(namespaced_xml, parser=parser))
            )
            parent.replace(element, namespaced_xml_node)
            # return result
    elif isinstance(element, ET._ElementUnicodeResult):
        if not isinstance(attributes, str):
            raise ValueError(
                f"Invalid query 'attributes' type: {type(attributes)} for direct attribute/text update, must be of type {str}."
            )
        return _update_unicode_result(attributes, element)
    else:
        raise ValueError(f"Unknown element type {type(element)}.")


def _update_unicode_result(
    attributes: Dict[str, Any], element: ET._ElementUnicodeResult
):
    parent = element.getparent()
    if element.is_text:
        parent.text = str(attributes)
        return str(element)
    elif element.is_attribute:
        parent.set(element.attrname, str(attributes))
        return {element.attrname: _xml_to_primitive(str(element))}
    else:
        raise ValueError(f"Unknown element: {element}, failed to update.")
