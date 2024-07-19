"""Unit tests for the @attempt decorator."""

import unittest
from star_ray.utils import TypeRouter
from star_ray.agent import Actuator, attempt


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


class TestAttempt(unittest.TestCase):
    """@attempt unit tests."""

    def test_attempt_type_routing(self):
        """Test the `@attempt` decorator with arguments."""

        # Define attempt-decorated functions
        class MyActuator(Actuator):
            @attempt([A])
            def func_a(self, e):
                return f"func_a: {type(e).__name__}"

            @attempt([C])
            def func_c(self, e):
                return f"func_c: {type(e).__name__}"

        actuator = MyActuator()

        print(actuator.func_a.route_types)
        # Initialize TypeRouter
        router = TypeRouter()
        router.add(actuator.func_a)
        router.add(actuator.func_c)

        # Test routing for various types
        self.assertEqual(router(A()), ["func_a: A"])
        self.assertEqual(router(B()), ["func_a: B"])
        self.assertEqual(router(C()), ["func_c: C"])
        self.assertEqual(router(D()), ["func_c: D"])
        self.assertEqual(router(E()), [])
        self.assertListEqual(
            ["func_a: A", "func_a: B", "func_c: C", "func_c: D"],
            list(actuator.iter_actions()),
        )

    def test_attempt_with_typehints(self):
        """Test the `@attempt` decorator using type hints."""

        # Define attempt-decorated functions
        class MyActuator(Actuator):
            @attempt
            def func_a(self, e: A):
                return f"func_a: {type(e).__name__}"

            @attempt()
            def func_ab(self, e: A | B):
                return f"func_ab: {type(e).__name__}"

        actuator = MyActuator()

        # Initialize TypeRouter
        router = TypeRouter()
        router.add(actuator.func_a)
        router.add(actuator.func_ab)

        # Test routing for various types
        self.assertEqual(router(A()), ["func_a: A", "func_ab: A"])
        # func_a will not be called because a function for B was found!
        self.assertEqual(router(B()), ["func_ab: B"])
        self.assertEqual(router(E()), [])

        self.assertListEqual(
            ["func_a: A", "func_ab: A", "func_ab: B"], list(actuator.iter_actions())
        )


if __name__ == "__main__":
    unittest.main()
