import unittest
from icua2.environment.xml import XMLState, QueryXPath

NAMESPACES = {"svg": "http://www.w3.org/2000/svg"}


class TestXMLStateXPath(unittest.TestCase):
    def test_select_elements(self):
        svg_code = """<svg id="root" xmlns="http://www.w3.org/2000/svg"> <rect id="rect-1" width="100"/> <rect id="rect-2" width="200"/> </svg>"""
        app = XMLState(svg_code, namespaces=NAMESPACES)
        query = QueryXPath.new_select("//svg:rect")
        result = app.__query__(query)
        self.assertListEqual(
            result.data,
            [
                '<rect xmlns="http://www.w3.org/2000/svg" id="rect-1" width="100"/>',
                '<rect xmlns="http://www.w3.org/2000/svg" id="rect-2" width="200"/>',
            ],
        )

    def test_select_text_from_element(self):
        svg_code = """<svg id="root" xmlns="http://www.w3.org/2000/svg"> <g> Some text! </g> <rect id="rect-1" width="100"/> <rect id="rect-2" width="200"/> </svg>"""
        app = XMLState(svg_code, namespaces=NAMESPACES)
        query = QueryXPath.new_select("//svg:g/text()")
        result = app.__query__(query)
        self.assertEqual(len(result.data), 1)
        self.assertEqual(result.data[0], " Some text! ")

    def test_select_multiple_attributes(self):
        svg_code = """<svg id="root" xmlns="http://www.w3.org/2000/svg"> <rect id="rect-1" width="100" height="200"/> </svg>"""
        app = XMLState(svg_code, namespaces=NAMESPACES)
        query = QueryXPath.new_select("//svg:rect", ["id", "width", "height"])
        result = app.__query__(query)
        self.assertListEqual(
            result.data, [{"id": "rect-1", "width": 100, "height": 200}]
        )

    def test_select_multiple_attributes_from_multiple_elements(self):
        svg_code = """<svg id="root" xmlns="http://www.w3.org/2000/svg"> <rect id="rect-1" width="100" height="200"/> <rect id="rect-2" width="200" height="300"/> </svg>"""
        app = XMLState(svg_code, namespaces=NAMESPACES)
        query = QueryXPath.new_select("//svg:rect", ["id", "width", "height"])
        result = app.__query__(query)
        self.assertListEqual(
            result.data,
            [
                {"id": "rect-1", "width": 100, "height": 200},
                {"id": "rect-2", "width": 200, "height": 300},
            ],
        )

    def test_select_by_xpath_only(self):
        svg_code = """<svg id="root" xmlns="http://www.w3.org/2000/svg"> <rect id="rect-1" width="100" height="200"/> </svg>"""
        app = XMLState(svg_code, namespaces=NAMESPACES)
        query = QueryXPath.new_select("//svg:rect", ["height"])
        result1 = app.__query__(query)
        query = QueryXPath.new_select("//svg:rect/attribute::height")
        result2 = app.__query__(query)
        self.assertListEqual(result1.data, result2.data)

    def test_update_attribute(self):
        svg_code = """<svg id="root" xmlns="http://www.w3.org/2000/svg"> <rect id="rect-1" width="100" height="200"/> </svg>"""
        app = XMLState(svg_code, namespaces=NAMESPACES)
        query = QueryXPath.new_update("//svg:rect", {"height": 400})
        result = app.__query__(query)
        query = QueryXPath.new_select("//svg:rect/attribute::height")
        result = app.__query__(query)
        self.assertListEqual(result.data, [{"height": 400}])

    def test_update_attribute_with_xpath(self):
        svg_code = """<svg id="root" xmlns="http://www.w3.org/2000/svg"> <rect id="rect-1" width="100" height="200"/> </svg>"""
        app = XMLState(svg_code, namespaces=NAMESPACES)
        query = QueryXPath.new_update("//svg:rect/attribute::height", "400")
        result = app.__query__(query)
        query = QueryXPath.new_select("//svg:rect/attribute::height")
        result = app.__query__(query)
        self.assertListEqual(result.data, [{"height": 400}])

    def test_update_multiple_attributes(self):
        svg_code = """<svg id="root" xmlns="http://www.w3.org/2000/svg"> <rect id="rect-1" width="100" height="200"/> <rect id="rect-2" width="100" height="300"/> </svg>"""
        app = XMLState(svg_code, namespaces=NAMESPACES)
        query = QueryXPath.new_update("//svg:rect", {"height": 400})
        result = app.__query__(query)
        query = QueryXPath.new_select("//svg:rect/attribute::height")
        result = app.__query__(query)
        self.assertListEqual(result.data, [{"height": 400}, {"height": 400}])

    def test_update_text(self):
        svg_code = """<svg id="root" xmlns="http://www.w3.org/2000/svg"> <g> Some text! </g> <rect id="rect-1" width="100"/> <rect id="rect-2" width="200"/> </svg>"""
        app = XMLState(svg_code, namespaces=NAMESPACES)
        query = QueryXPath.new_update("//svg:g/text()", "some new text!")
        result = app.__query__(query)
        self.assertListEqual(result.data, [" Some text! "])

        query = QueryXPath.new_select("//svg:g/text()")
        result = app.__query__(query)
        self.assertListEqual(result.data, ["some new text!"])

    def test_update_element(self):
        svg_code = """<svg id="root" xmlns="http://www.w3.org/2000/svg"> <g id="mygroup"> Some text! </g> <g id="myothergroup"> Some other text! </g></svg>"""
        app = XMLState(svg_code, namespaces=NAMESPACES)
        query = QueryXPath.new_update(
            """//svg:g[@id="mygroup"]""",
            """<svg:g id="mynewgroup"> Some new text! </svg:g>""",
        )
        result = app.__query__(query)
        self.assertTrue(result.success)
        query = QueryXPath.new_select("//svg:g")
        result = app.__query__(query)
        self.assertTrue(result.success)
        self.assertListEqual(
            result.data,
            [
                '<g xmlns="http://www.w3.org/2000/svg" id="mynewgroup"> Some new text! </g>',
                '<g xmlns="http://www.w3.org/2000/svg" id="myothergroup"> Some other text! </g>',
            ],
        )


if __name__ == "__main__":
    unittest.main()
