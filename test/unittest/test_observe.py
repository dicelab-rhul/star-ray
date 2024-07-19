"""Unit tests for the @observe decorator."""

import unittest
from star_ray.agent import observe
from star_ray.utils import TypeRouter


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


class TestObserve(unittest.TestCase):
    """@observe unit tests."""

    def test_observe(self):
        """Test the `@observe` decorator with arguments."""

        # Define observe-decorated functions
        @observe([A])
        def func_a(e):
            return f"func_a: {type(e).__name__}"

        @observe([C])
        def func_c(e):
            return f"func_c: {type(e).__name__}"

        # Initialize TypeRouter
        router = TypeRouter()
        router.add(func_a)
        router.add(func_c)

        # Test routing for various types
        self.assertEqual(router(A()), ["func_a: A"])
        self.assertEqual(router(B()), ["func_a: B"])
        self.assertEqual(router(C()), ["func_c: C"])
        self.assertEqual(router(D()), ["func_c: D"])
        self.assertEqual(router(E()), [])

    def test_observe2(self):
        """Test the `@observe` decorator with arguments."""

        # Define observe-decorated functions
        @observe([B])
        def func_b(e):
            return f"func_b: {type(e).__name__}"

        @observe([C])
        def func_c(e):
            return f"func_c: {type(e).__name__}"

        # Initialize TypeRouter
        router = TypeRouter()
        router.add(func_b)
        router.add(func_c)

        # Test routing for various types
        self.assertEqual(router(A()), [])
        self.assertEqual(router(B()), ["func_b: B"])
        self.assertEqual(router(C()), ["func_c: C"])
        self.assertEqual(router(D()), ["func_b: D"])
        self.assertEqual(router(E()), [])

    def test_observe_with_typehints(self):
        """Test the `@observe` decorator using type hints."""

        @observe
        def func_a(e: A):
            return f"func_a: {type(e).__name__}"

        @observe
        def func_ab(e: A | B):
            return f"func_ab: {type(e).__name__}"

        # Initialize TypeRouter
        router = TypeRouter()
        router.add(func_a)
        router.add(func_ab)

        # Test routing for various types
        self.assertEqual(router(A()), ["func_a: A", "func_ab: A"])
        # func_a will not be called because a function for B was found!
        self.assertEqual(router(B()), ["func_ab: B"])
        self.assertEqual(router(E()), [])


if __name__ == "__main__":
    unittest.main()
