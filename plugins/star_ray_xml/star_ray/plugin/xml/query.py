""" TODO """

from typing import Dict, List, Any
from lxml import etree as ET
from star_ray.event import Action

from typing import TYPE_CHECKING
from .utils import xml_element_to_string, xml_to_primitive
from .xml_state import XMLState

if TYPE_CHECKING:
    from .query_xpath import QueryXPath


class XPathQuery(Action):
    xpath: str


class Insert(XPathQuery):

    element: str


class Delete(XPathQuery):
    pass


class Update(XPathQuery):

    values: str | Dict[str, Any]


class Select(XPathQuery):

    values: List[str]


# def _select(
#     query: "QueryXPath",
#     state: "XMLState",
# ):
#     # pylint: disable=W0212
#     elements = state._root.xpath(query.xpath, namespaces=state._namespaces)
#     # TODO some xpath queries do not return a list of elements, they may return a value (e.g. a float from `count()`)
#     if isinstance(elements, (int, float, bool, str)):
#         return elements
#     elif isinstance(elements, (ET._Element, ET._ElementUnicodeResult)):
#         return XMLState._select_element(query.attributes, elements)
#     else:
#         return [
#             XMLState._select_element(query.attributes, element) for element in elements
#         ]


@staticmethod
def _select_element(attributes: List[str], element: ET.ElementBase):
    if isinstance(element, ET._Element):
        if len(attributes) > 0:
            # TODO rather than none, return a Missing object?
            return {
                attrib: xml_to_primitive(element.get(attrib, None))
                for attrib in attributes
            }
        else:
            # return the XML element itself!
            return xml_element_to_string(element)
    elif isinstance(element, ET._ElementUnicodeResult):
        if element.is_attribute:
            return {element.attrname: xml_to_primitive(str(element))}
        else:
            return str(element)
    else:
        raise ValueError(f"Unknown element type {type(element)}.")


# @staticmethod
# def _update(
#     query: "QueryXPath",
#     state: "XMLState",
# ):
#     # pylint: disable=W0212
#     elements = state._root.xpath(query.xpath, namespaces=state._namespaces)
#     _ = [
#         XMLState._update_element(
#             query.attributes,
#             element,
#             namespaces=state._namespaces,
#             parser=state._parser,
#         )
#         for element in elements
#     ]


@staticmethod
def _update_element(
    attributes: Dict[str, Any],
    element: ET.ElementBase,
    namespaces: Dict[str, str] = None,
    parser: ET.XMLParser = None,
):
    if isinstance(element, ET._Element):
        if isinstance(attributes, dict):
            assert len(attributes) > 0
            # TODO rather than none, return a Missing object?
            # result = {
            #     attrib: xml_to_primitive(element.get(attrib, None))
            #     for attrib in attributes
            # }
            for attrib, value in attributes.items():
                # TODO raise a warning if the attribute doesnt exist? what to do here...
                element.set(attrib, str(value))
            # return result
        elif isinstance(attributes, str):
            # we are updating the element itself
            parent = element.getparent()
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
        return XMLState._update_unicode_result(attributes, element)
    else:
        raise ValueError(f"Unknown element type {type(element)}.")


@staticmethod
def _update_unicode_result(
    attributes: Dict[str, Any], element: ET._ElementUnicodeResult
):
    parent = element.getparent()
    if element.is_text:
        parent.text = str(attributes)
        return str(element)
    elif element.is_attribute:
        parent.set(element.attrname, str(attributes))
        return {element.attrname: xml_to_primitive(str(element))}
    else:
        raise ValueError(f"Unknown element: {element}, failed to update.")
