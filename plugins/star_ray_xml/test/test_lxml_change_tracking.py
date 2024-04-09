import unittest
from pprint import pprint

# pylint: disable=E0401, E0611
from star_ray.plugin.xml import (
    QueryXPath,
    QueryXMLHistory,
    XMLAmbient,
    xml_history,
)

NAMESPACES = {"svg": "http://www.w3.org/2000/svg"}

XML = """
<svg width="200" height="200" xmlns="http://www.w3.org/2000/svg">
    <g>
        <!-- Circle 1 -->
        <circle cx="50" cy="50" r="30" fill="red" />
        <!-- Circle 2 -->
        <circle cx="150" cy="50" r="30" fill="green" />
    </g>
        <!-- Rectangle 1 -->
        <rect x="130" y="20" width="50" height="30" fill="orange" />
</svg>
"""


class TestXMLChangeHistory(unittest.TestCase):

    def test_update_store(self):

        @xml_history(force_overwrite=True)
        class MyXMLAmbient(XMLAmbient):
            pass

        ambient = MyXMLAmbient([], xml=XML, namespaces=NAMESPACES)
        query = QueryXPath(xpath="//svg:circle", attributes={"cx": 10, "cy": 10})
        # update cx and cy
        ambient.__update__(query)
        # check that history
        query = QueryXMLHistory.new("test")
        response = ambient.__select__(query)
        pprint(response)

        # TODO assert that that response is correct!


if __name__ == "__main__":
    unittest.main()
