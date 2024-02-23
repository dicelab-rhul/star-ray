import re
import unittest


def split_path(path):
    # Regular expression to match '/' outside curly brackets
    pattern = r"/(?![^{]*})"

    # Split the path based on the pattern
    parts = re.split(pattern, path)

    # Regular expression pattern to extract URI and element
    uri_element_pattern = r"(?:\{([^{}]*)\})?(.*)"

    # Extract URI and element for each part
    result = []
    for part in parts:
        match = re.match(uri_element_pattern, part)
        if match:
            uri, element = match.groups()
            result.append((uri, element))
        else:
            result.append((None, part))
    print(result)
    return result


class TestSplitPath(unittest.TestCase):
    def test_basic_input(self):
        input_path = (
            "{http://www.w3.org/2000/svg}g/{http://www.w3.org/2000/svg}circle[2]"
        )
        expected_output = [
            ("http://www.w3.org/2000/svg", "g"),
            ("http://www.w3.org/2000/svg", "circle[2]"),
        ]
        self.assertEqual(split_path(input_path), expected_output)

    def test_multiple_nesting_levels(self):
        input_path = "{http://www.w3.org/2000/svg}g/{http://www.w3.org/2000/svg}rect/{http://www.w3.org/2000/svg}text[1]"
        expected_output = [
            ("http://www.w3.org/2000/svg", "g"),
            ("http://www.w3.org/2000/svg", "rect"),
            ("http://www.w3.org/2000/svg", "text[1]"),
        ]
        self.assertEqual(split_path(input_path), expected_output)

    def test_wildcard_and_namespace(self):
        input_path = "./*[1]/*/{http://www.example.com/ns}test/test2"
        expected_output = [
            (None, "."),
            (None, "*[1]"),
            (None, "*"),
            ("http://www.example.com/ns", "test"),
            (None, "test2"),
        ]
        self.assertEqual(split_path(input_path), expected_output)

    def test_no_namespace(self):
        input_path = "g/circle[1]"
        expected_output = [(None, "g"), (None, "circle[1]")]
        self.assertEqual(split_path(input_path), expected_output)

    def test_path_with_leading_and_trailing_slashes(self):
        input_path = (
            "/{http://www.w3.org/2000/svg}g/{http://www.w3.org/2000/svg}circle[2]"
        )
        expected_output = [
            (None, ""),
            ("http://www.w3.org/2000/svg", "g"),
            ("http://www.w3.org/2000/svg", "circle[2]"),
        ]
        self.assertEqual(split_path(input_path), expected_output)

    def test_empty_input(self):
        input_path = ""
        expected_output = [(None, "")]
        self.assertEqual(split_path(input_path), expected_output)


if __name__ == "__main__":
    unittest.main()
