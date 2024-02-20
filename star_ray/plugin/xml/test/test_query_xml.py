import unittest
from star_ray.plugin.xml import XMLState, QueryXML

NAMESPACES = {"svg": "http://www.w3.org/2000/svg"}


class TestXMLState(unittest.TestCase):
    def test_select(self):
        svg_code = """<svg id="root" xmlns="http://www.w3.org/2000/svg"> hello [[myworldtext]] <!-- Background rectangle --> <rect id="[[id]]" width="[[100 + rect.size.0]]" height="[[rect.size.1]]" fill="#f5f5f5"/> </svg>"""
        app = XMLState(svg_code, namespaces=NAMESPACES)
        query = QueryXML.new("test", "[[id]]", ["width", "height"])
        result = app.__select__(query)
        self.assertTrue(result.success)
        self.assertTupleEqual(
            result.values,
            (
                "[[id]]",
                {
                    "width": "[[100 + rect.size.0]]",
                    "height": "[[rect.size.1]]",
                },
            ),
        )

    def test_select_root(self):
        svg_code = """<svg id="root" xmlns="http://www.w3.org/2000/svg"> hello [[myworldtext]] <!-- Background rectangle --> <rect id="[[id]]" width="[[100 + rect.size.0]]" height="[[rect.size.1]]" fill="#f5f5f5"/> </svg>"""
        app = XMLState(svg_code, namespaces=NAMESPACES)
        query = QueryXML.new("test", "root", [])
        result = app.__select__(query)
        self.assertTrue(result.success)
        self.assertTupleEqual(
            result.values,
            (
                "root",
                '<svg xmlns="http://www.w3.org/2000/svg" id="root"> hello [[myworldtext]] <!-- Background rectangle --> <rect id="[[id]]" width="[[100 + rect.size.0]]" height="[[rect.size.1]]" fill="#f5f5f5"/> </svg>',
            ),
        )

    def test_select_error_id_missing(self):
        svg_code = """<svg id="root" xmlns="http://www.w3.org/2000/svg"> hello [[myworldtext]] <!-- Background rectangle --> <rect id="[[id]]" width="[[100 + rect.size.0]]" height="[[rect.size.1]]" fill="#f5f5f5"/> </svg>"""
        app = XMLState(svg_code, namespaces=NAMESPACES)
        query = QueryXML.new("test", "invalid_id", ["width", "height"])
        response = app.__select__(query)
        self.assertFalse(response.success)
        self.assertTrue(isinstance(response.error, Exception))  # pylint: disable=E1101

    def test_select_error_id_not_unique(self):
        svg_code = """<svg id="root" xmlns="http://www.w3.org/2000/svg"> hello [[myworldtext]] <!-- Background rectangle --> <rect id="[[id]]"/> <rect id="[[id]]"/> </svg>"""
        app = XMLState(svg_code, namespaces=NAMESPACES)
        query = QueryXML.new("test", "[[id]]", [])
        response = app.__select__(query)
        self.assertFalse(response.success)
        self.assertTrue(isinstance(response.error, Exception))  # pylint: disable=E1101

    def test_update(self):
        svg_code = """<svg id="root" xmlns="http://www.w3.org/2000/svg"> hello [[myworldtext]] <!-- Background rectangle --> <rect id="[[id]]" width="[[100 + rect.size.0]]" height="[[rect.size.1]]" fill="#f5f5f5"/> </svg>"""
        app = XMLState(svg_code, namespaces=NAMESPACES)
        query = QueryXML.new("test", "[[id]]", {"width": 100, "height": 200})
        result = app.__update__(query)
        self.assertTrue(result.success)
        query = QueryXML.new("test", "[[id]]", ["width", "height"])
        result = app.__select__(query)
        self.assertTrue(result.success)
        self.assertTupleEqual(
            result.values,
            (
                "[[id]]",
                {
                    "width": 100,
                    "height": 200,
                },
            ),
        )


if __name__ == "__main__":
    unittest.main()
