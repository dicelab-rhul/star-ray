import unittest
from typing import Dict, Any
from lxml import etree as ET

from star_ray.plugin.xml import XMLState, QueryXPath
from star_ray.plugin.xml.query import _select_element, _update_element


@staticmethod
def _update_element(
    attributes: Dict[str, Any],
    element: ET.ElementBase,
    namespaces: Dict[str, str] = None,
    parser: ET.XMLParser = None,
):
    print(type(element))
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


NAMESPACES = {"svg": "http://www.w3.org/2000/svg"}

# XPATH REPLACE
# str -> str
# int -> int
# float -> float
# Element -> str

# XPATH UPDATE
# Element -> Dict (attributes)
# Element -> str (namespace:tag)


class TestXMLState(unittest.TestCase):

    def test_update_element(self):
        xml = """<svg id="root" xmlns="http://www.w3.org/2000/svg"> <rect id="rect-1" width="100"/> <rect id="rect-2" width="200"/> </svg>"""
        xml = """<svg id="root" xmlns="http://www.w3.org/2000/svg"> hi </svg>"""

        root = ET.fromstring(xml)
        element = root.xpath("/svg:svg/child:node()", namespaces=NAMESPACES)
        print(element)

        result = _update_element({"id": "newroot"}, element, namespaces=NAMESPACES)
        print(result)


if __name__ == "__main__":
    unittest.main()
