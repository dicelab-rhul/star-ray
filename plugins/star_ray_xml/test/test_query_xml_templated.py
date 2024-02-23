import unittest
from star_ray.event.responseevent import ErrorResponse
from star_ray.plugin.star_ray_xml import XMLState, QueryXMLTemplated, QueryXML

NAMESPACES = {"svg": "http://www.w3.org/2000/svg"}


class TestQueryXMLTemplated(unittest.TestCase):

    def test_select_empty_error(self):
        with self.assertRaises(ValueError):
            QueryXMLTemplated.new("test", "[[id]]", [])

    def test_select_error_undefined_template_variable(self):
        svg_code = """<svg id="root" xmlns="http://www.w3.org/2000/svg"> <rect id="myrect" data-index="1" data-1="a" data-2="b"/> </svg>"""
        app = XMLState(svg_code, namespaces=NAMESPACES)
        # note the change from "-" to "_" on attribute names. This is to ensure the template can be properly resolved by jinja!
        query = QueryXMLTemplated.new("test", "myrect", ["{{data-index}}"])
        response = app.__select__(query)
        self.assertIsInstance(response, ErrorResponse)

    def test_select_error_element_attribute_doesnt_exist(self):
        svg_code = """<svg id="root" xmlns="http://www.w3.org/2000/svg"> <rect id="myrect" data-index="1" data-1="a" data-2="b"/> </svg>"""
        app = XMLState(svg_code, namespaces=NAMESPACES)
        # note the change from "-" to "_" on attribute names. This is to ensure the template can be properly resolved by jinja!
        query = QueryXMLTemplated.new("test", "myrect", ["{{data_index}}"])
        response = app.__select__(query)
        self.assertIsInstance(response, ErrorResponse)

    def test_select(self):
        svg_code = """<svg id="root" xmlns="http://www.w3.org/2000/svg"> <rect id="myrect" data-index="1" data-1="a" data-2="b"/> </svg>"""
        app = XMLState(svg_code, namespaces=NAMESPACES)
        # note the change from "-" to "_" on attribute names in a template!, this is to ensure they can be properly resolved by jinja!
        # otherwise, the resulting attribute in select should have the same name as the element attribute, here for example "data-1"
        query = QueryXMLTemplated.new("test", "myrect", ["data-{{data_index}}"])
        response = app.__select__(query)
        self.assertDictEqual(response.values, {"data-1": "a"})

    def test_update(self):
        svg_code = """<svg id="root" xmlns="http://www.w3.org/2000/svg"> <rect id="myrect" data-index="1" data-1="a" data-2="b"/> </svg>"""
        app = XMLState(svg_code, namespaces=NAMESPACES)
        # this query will set the value of data-1 to the value of data-2. data-1 is resolved using data-index
        query = QueryXMLTemplated.new(
            "test", "myrect", {"data-{{data_index}}": "{{data_2}}"}
        )
        result = app.__update__(query)
        self.assertTrue(result.success)

        # note that no template was used here, it still works - not all select attributes need to be templates
        # we should prefer to use QueryXML in this case.
        query = QueryXMLTemplated.new("test", "myrect", ["data-1"])
        result = app.__select__(query)
        self.assertDictEqual(result.values, {"data-1": "b"})

    def test_update_replace_element(self):
        svg_code = """<svg id="root" xmlns="http://www.w3.org/2000/svg"> <rect id="myrect" data-index="1" data-1="a" data-2="b"/> </svg>"""
        app = XMLState(svg_code, namespaces=NAMESPACES)
        # this query will replace the entire element "myrect" with a new element that is based on "myrects current values"
        query = QueryXMLTemplated.new(
            "test",
            "myrect",
            """<rect id="mynewrect" data-index="1" data-1="{{data_2}}" data-2="{{data_1}}"/>""",
        )

        result = app.__update__(query)
        self.assertTrue(result.success)

        # # note that no template was used here, it still works - not all select attributes need to be templates
        # # we should prefer to use QueryXML in this case.
        query = QueryXML.new("test", "mynewrect", ["data-1", "data-2"])
        result = app.__select__(query)
        print(result)
        # self.assertDictEqual(result.values, {"data-1": "b"})


if __name__ == "__main__":
    unittest.main()
