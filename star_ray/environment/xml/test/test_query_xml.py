import unittest
from icua2.environment.xml import XMLState, QueryXML

NAMESPACES = {"svg": "http://www.w3.org/2000/svg"}


class TestXMLState(unittest.TestCase):
    def test_select(self):
        svg_code = """<svg id="root" xmlns="http://www.w3.org/2000/svg"> hello [[myworldtext]] <!-- Background rectangle --> <rect id="[[id]]" width="[[100 + rect.size.0]]" height="[[rect.size.1]]" fill="#f5f5f5"/> </svg>"""
        app = XMLState(svg_code, namespaces=NAMESPACES)
        query = QueryXML.new("[[id]]", ["width", "height"])
        result = app.__query__(query)
        self.assertTrue(result.success)
        self.assertDictEqual(
            result.data,
            {
                "[[id]]": {
                    "width": "[[100 + rect.size.0]]",
                    "height": "[[rect.size.1]]",
                }
            },
        )

    def test_select_root(self):
        svg_code = """<svg id="root" xmlns="http://www.w3.org/2000/svg"> hello [[myworldtext]] <!-- Background rectangle --> <rect id="[[id]]" width="[[100 + rect.size.0]]" height="[[rect.size.1]]" fill="#f5f5f5"/> </svg>"""
        app = XMLState(svg_code, namespaces=NAMESPACES)
        query = QueryXML.new("root", [])
        result = app.__query__(query)
        self.assertTrue(result.success)
        self.assertDictEqual(
            result.data,
            {
                "root": '<svg xmlns="http://www.w3.org/2000/svg" id="root"> hello [[myworldtext]] <!-- Background rectangle --> <rect id="[[id]]" width="[[100 + rect.size.0]]" height="[[rect.size.1]]" fill="#f5f5f5"/> </svg>'
            },
        )

    def test_select_error_id_missing(self):
        svg_code = """<svg id="root" xmlns="http://www.w3.org/2000/svg"> hello [[myworldtext]] <!-- Background rectangle --> <rect id="[[id]]" width="[[100 + rect.size.0]]" height="[[rect.size.1]]" fill="#f5f5f5"/> </svg>"""
        app = XMLState(svg_code, namespaces=NAMESPACES)
        query = QueryXML.new("invalid_id", ["width", "height"])
        response = app.__query__(query)
        self.assertFalse(response.success)
        self.assertTrue(isinstance(response.error, Exception))

    def test_select_error_id_not_unique(self):
        svg_code = """<svg id="root" xmlns="http://www.w3.org/2000/svg"> hello [[myworldtext]] <!-- Background rectangle --> <rect id="[[id]]"/> <rect id="[[id]]"/> </svg>"""
        app = XMLState(svg_code, namespaces=NAMESPACES)
        query = QueryXML.new("[[id]]", [])
        response = app.__query__(query)
        self.assertFalse(response.success)
        self.assertTrue(isinstance(response.error, Exception))

    def test_update(self):
        svg_code = """<svg id="root" xmlns="http://www.w3.org/2000/svg"> hello [[myworldtext]] <!-- Background rectangle --> <rect id="[[id]]" width="[[100 + rect.size.0]]" height="[[rect.size.1]]" fill="#f5f5f5"/> </svg>"""
        app = XMLState(svg_code, namespaces=NAMESPACES)
        query = QueryXML.new("[[id]]", {"width": 100, "height": 200})
        result = app.__query__(query)
        self.assertTrue(result.success)
        # result should contain the old, newly updated values
        self.assertDictEqual(
            result.data,
            {
                "[[id]]": {
                    "width": "[[100 + rect.size.0]]",
                    "height": "[[rect.size.1]]",
                }
            },
        )
        query = QueryXML.new("[[id]]", ["width", "height"])
        result = app.__query__(query)
        self.assertTrue(result.success)
        self.assertDictEqual(
            result.data,
            {
                "[[id]]": {
                    "width": 100,
                    "height": 200,
                }
            },
        )


if __name__ == "__main__":
    unittest.main()
