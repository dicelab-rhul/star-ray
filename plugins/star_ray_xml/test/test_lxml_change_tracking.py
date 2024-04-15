import unittest
from lxml import etree
from star_ray.plugin.xml import xml_change_tracker
from star_ray.plugin.xml import xml_history, QueryXMLHistory

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


@xml_change_tracker
class XMLStateStub:
    def __init__(self, parser=None, **kwargs):
        super().__init__()
        self.parser = parser

    def fromstring(self, xml):
        return etree.fromstring(xml, parser=self.parser)


@xml_history(use_disk=False)
class XMLStateStub2:
    def __init__(self, parser=None, **kwargs):
        super().__init__()
        self.parser = parser

    def fromstring(self, xml):
        return etree.fromstring(xml, parser=self.parser)


class TestXMLHistory(unittest.TestCase):

    def test_history(self):
        stub = XMLStateStub2()
        root = stub.fromstring(XML)

        children = root.xpath("//svg:circle", namespaces=NAMESPACES)
        for child in children:
            child.set("cx", "10")
            child.set("cy", "20")
        # pylint: disable=E1101
        results = stub.__select__(QueryXMLHistory(index=...)).values
        self.assertEqual(len(results), 4)
        for result in results:
            response = root.xpath(result["xpath"], namespaces=NAMESPACES)
            self.assertEqual(len(response), 1)
            self.assertEqual(response[0].tag, "{http://www.w3.org/2000/svg}circle")


class TestXMLChangeTracking(unittest.TestCase):

    def test_change_attribute(self):
        results = []

        def _callback(event):
            results.append(event)

        stub = XMLStateStub()
        # pylint: disable=E1101
        stub.add_xml_change_callback(_callback)
        root = stub.fromstring(XML)

        children = root.xpath("//svg:circle", namespaces=NAMESPACES)
        for child in children:
            child.set("cx", "10")
            child.set("cy", "20")
        self.assertEqual(len(results), 4)
        for result in results:
            response = root.xpath(result["xpath"], namespaces=NAMESPACES)
            self.assertEqual(len(response), 1)
            self.assertEqual(response[0].tag, "{http://www.w3.org/2000/svg}circle")


if __name__ == "__main__":
    unittest.main()
