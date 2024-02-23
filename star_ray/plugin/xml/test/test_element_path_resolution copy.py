import re
import unittest


def split_path(path):
    # Regular expression to match text between curly brackets and text after the brackets
    # pattern = r"\{([^{}]*)\}(?:([^/{}]*))"
    pattern = r"(?:\{([^{}]*)\})?(?:([^/{}]*))"

    # Find all matches of groups in the element path
    matches = re.findall(pattern, path)
    print(matches)
    return matches


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
        input_path = "./*[1]/*/{http://www.example.com/ns}test"
        expected_output = [
            ("", "*"),
            ("", "[1]"),
            ("", "*"),
            ("http://www.example.com/ns", "test"),
        ]
        self.assertEqual(split_path(input_path), expected_output)

    # def test_no_namespace(self):
    #     input_path = "g/circle[1]"
    #     expected_output = [("", "g"), ("", "circle[1]")]
    #     self.assertEqual(split_path(input_path), expected_output)

    # def test_path_with_leading_and_trailing_slashes(self):
    #     input_path = (
    #         "/{http://www.w3.org/2000/svg}g/{http://www.w3.org/2000/svg}circle[2]/"
    #     )
    #     expected_output = [
    #         ("http://www.w3.org/2000/svg", "g"),
    #         ("http://www.w3.org/2000/svg", "circle[2]"),
    #     ]
    #     self.assertEqual(split_path(input_path), expected_output)

    # def test_empty_input(self):
    #     input_path = ""
    #     expected_output = []
    #     self.assertEqual(split_path(input_path), expected_output)


if __name__ == "__main__":
    unittest.main()
