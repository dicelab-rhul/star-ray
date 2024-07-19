"""Unit tests for the `TypeRouter` class."""

import unittest
from typing import Any
from star_ray.utils.type_routing import TypeRouter


class A:  # noqa: D101
    pass


class B(A):  # noqa: D101
    pass


class C(A):  # noqa: D101
    pass


class D(B, C):  # noqa: D101
    pass


class E:  # noqa: D101
    pass


class TestTypeRouting(unittest.TestCase):
    """TypeRouter unit tests."""

    def test_resolve_types(self):
        """Test the `resolve_route_types` method."""
        result = TypeRouter.resolve_route_types(
            [list, list, dict[str, Any], tuple, Any, int | str]
        )
        self.assertListEqual(result, [list, list, dict, tuple, Any, int, str])

    def test_resolve_first_argument_types(self):
        """Test the `resolve_first_argument_types` method."""

        def myfunc1(self, x: list[str], y: object, z: int, w: Any) -> float:
            pass

        def myfunc2(x: str, y: object, z: int, w: Any) -> float:
            pass

        TypeAlias = str | int | list[str]

        def myfunc3(x: TypeAlias) -> float:  # type: ignore
            pass

        result = TypeRouter.resolve_first_argument_types(myfunc1)
        self.assertListEqual(result, [list])
        result = TypeRouter.resolve_first_argument_types(myfunc2)
        self.assertListEqual(result, [str])
        result = TypeRouter.resolve_first_argument_types(myfunc3)
        self.assertListEqual(result, [str, int, list])

    def test_resolve_first_argument_types_error(self):
        """Test the `@observe` decorator, check error: without type hints."""

        class Test:
            def test(self, a):
                pass

        t = Test()
        with self.assertRaises(TypeError):
            TypeRouter.resolve_first_argument_types(t.test)


if __name__ == "__main__":
    unittest.main()
