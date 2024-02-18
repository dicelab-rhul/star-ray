# pylint: disable=E1101
from star_ray.plugin.xml import QueryXML, XMLAmbient
from star_ray.event.listener import change_listener
import unittest

NAMESPACES = {"svg": "http://www.w3.org/2000/svg"}


svg = """<svg id="root" xmlns="http://www.w3.org/2000/svg"> hello [[myworldtext]] <!-- Background rectangle --> <rect id="[[id]]" width="[[100 + rect.size.0]]" height="[[rect.size.1]]" fill="#f5f5f5"/> </svg>"""


@change_listener
class MyXMLAmbient(XMLAmbient):
    pass


ELEMENT_ID = "[[id]]"

ambient = MyXMLAmbient([], svg)
ambient.add_change_listener(my_change_listener)
query = QueryXML.new("test", ELEMENT_ID, {"width": 100, "height": 200})
ambient.__update__(query)
