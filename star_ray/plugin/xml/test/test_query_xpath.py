import unittest
from star_ray.plugin.xml import XMLState, QueryXPath

NAMESPACES = {"svg": "http://www.w3.org/2000/svg"}


class TestXMLStateXPath(unittest.TestCase):

    def test_select_with_str_error(self):
        svg_code = """<svg id="root" xmlns="http://www.w3.org/2000/svg"> <rect id="rect-1" width="100"/> <rect id="rect-2" width="200"/> </svg>"""
        app = XMLState(svg_code, namespaces=NAMESPACES)
        query = QueryXPath.new("test", "//svg:rect", "bad value...")
        result = app.__select__(query)

    def test_select_elements(self):
        svg_code = """<svg id="root" xmlns="http://www.w3.org/2000/svg"> <rect id="rect-1" width="100"/> <rect id="rect-2" width="200"/> </svg>"""
        app = XMLState(svg_code, namespaces=NAMESPACES)
        query = QueryXPath.new("test", "//svg:rect", [])
        result = app.__select__(query)
        self.assertListEqual(
            result.values,
            [
                '<rect xmlns="http://www.w3.org/2000/svg" id="rect-1" width="100"/>',
                '<rect xmlns="http://www.w3.org/2000/svg" id="rect-2" width="200"/>',
            ],
        )

    def test_select_text_from_element(self):
        svg_code = """<svg id="root" xmlns="http://www.w3.org/2000/svg"> <g> Some text! </g> <rect id="rect-1" width="100"/> <rect id="rect-2" width="200"/> </svg>"""
        app = XMLState(svg_code, namespaces=NAMESPACES)
        query = QueryXPath.new("test", "//svg:g/text()", [])
        result = app.__select__(query)
        self.assertEqual(len(result.values), 1)
        self.assertEqual(result.values[0], " Some text! ")

    def test_select_multiple_attributes(self):
        svg_code = """<svg id="root" xmlns="http://www.w3.org/2000/svg"> <rect id="rect-1" width="100" height="200"/> </svg>"""
        app = XMLState(svg_code, namespaces=NAMESPACES)
        query = QueryXPath.new("test", "//svg:rect", ["id", "width", "height"])
        result = app.__select__(query)
        self.assertListEqual(
            result.values, [{"id": "rect-1", "width": 100, "height": 200}]
        )

    def test_select_multiple_attributes_from_multiple_elements(self):
        svg_code = """<svg id="root" xmlns="http://www.w3.org/2000/svg"> <rect id="rect-1" width="100" height="200"/> <rect id="rect-2" width="200" height="300"/> </svg>"""
        app = XMLState(svg_code, namespaces=NAMESPACES)
        query = QueryXPath.new("test", "//svg:rect", ["id", "width", "height"])
        result = app.__select__(query)
        self.assertListEqual(
            result.values,
            [
                {"id": "rect-1", "width": 100, "height": 200},
                {"id": "rect-2", "width": 200, "height": 300},
            ],
        )

    def test_select_by_xpath_only(self):
        svg_code = """<svg id="root" xmlns="http://www.w3.org/2000/svg"> <rect id="rect-1" width="100" height="200"/> </svg>"""
        app = XMLState(svg_code, namespaces=NAMESPACES)
        query = QueryXPath.new("test", "//svg:rect", ["height"])
        result1 = app.__select__(query)
        query = QueryXPath.new("test", "//svg:rect/attribute::height", [])
        result2 = app.__select__(query)
        self.assertListEqual(result1.values, result2.values)

    def test_update_attribute(self):
        svg_code = """<svg id="root" xmlns="http://www.w3.org/2000/svg"> <rect id="rect-1" width="100" height="200"/> </svg>"""
        app = XMLState(svg_code, namespaces=NAMESPACES)
        query = QueryXPath.new("test", "//svg:rect", {"height": 400})
        result = app.__update__(query)
        query = QueryXPath.new("test", "//svg:rect/attribute::height", [])
        result = app.__select__(query)
        self.assertListEqual(result.values, [{"height": 400}])

    def test_update_attribute_with_xpath(self):
        svg_code = """<svg id="root" xmlns="http://www.w3.org/2000/svg"> <rect id="rect-1" width="100" height="200"/> </svg>"""
        app = XMLState(svg_code, namespaces=NAMESPACES)
        query = QueryXPath.new("test", "//svg:rect/attribute::height", "400")
        result = app.__update__(query)
        query = QueryXPath.new("test", "//svg:rect/attribute::height", [])
        result = app.__select__(query)
        self.assertListEqual(result.values, [{"height": 400}])

    def test_update_multiple_attributes(self):
        svg_code = """<svg id="root" xmlns="http://www.w3.org/2000/svg"> <rect id="rect-1" width="100" height="200"/> <rect id="rect-2" width="100" height="300"/> </svg>"""
        app = XMLState(svg_code, namespaces=NAMESPACES)
        query = QueryXPath.new("test", "//svg:rect", {"height": 400})
        result = app.__update__(query)
        query = QueryXPath.new("test", "//svg:rect/attribute::height", [])
        result = app.__select__(query)
        self.assertListEqual(result.values, [{"height": 400}, {"height": 400}])

    def test_update_text(self):
        svg_code = """<svg id="root" xmlns="http://www.w3.org/2000/svg"> <g> Some text! </g> <rect id="rect-1" width="100"/> <rect id="rect-2" width="200"/> </svg>"""
        app = XMLState(svg_code, namespaces=NAMESPACES)
        query = QueryXPath.new("test", "//svg:g/text()", "some new text!")
        result = app.__update__(query)
        query = QueryXPath.new("test", "//svg:g/text()", [])
        result = app.__select__(query)
        self.assertListEqual(result.values, ["some new text!"])

    def test_update_element(self):
        svg_code = """<svg id="root" xmlns="http://www.w3.org/2000/svg"> <g id="mygroup"> Some text! </g> <g id="myothergroup"> Some other text! </g></svg>"""
        app = XMLState(svg_code, namespaces=NAMESPACES)
        query = QueryXPath.new(
            "test",
            """//svg:g[@id="mygroup"]""",
            """<svg:g id="mynewgroup"> Some new text! </svg:g>""",
        )
        result = app.__update__(query)
        self.assertTrue(result.success)
        query = QueryXPath.new("test", "//svg:g", [])
        result = app.__select__(query)
        self.assertTrue(result.success)
        self.assertListEqual(
            result.values,
            [
                '<g xmlns="http://www.w3.org/2000/svg" id="mynewgroup"> Some new text! </g>',
                '<g xmlns="http://www.w3.org/2000/svg" id="myothergroup"> Some other text! </g>',
            ],
        )


if __name__ == "__main__":
    unittest.main()
