import unittest
from star_ray.agent.component.type_routing import _TypeRouter, attempt
from star_ray.agent import Actuator


class A:
    pass


class B(A):
    pass


class C(A):
    pass


class D(B, C):
    pass


class E:
    pass


class TestAttempt(unittest.TestCase):

    def test_attempt_type_routing(self):
        # Define observe-decorated functions
        class MyActuator(Actuator):

            @attempt([A])
            def func_a(self, e):
                return f"func_a: {type(e).__name__}"

            @attempt([C])
            def func_c(self, e):
                return f"func_c: {type(e).__name__}"
        actuator = MyActuator()

        # Initialize TypeRouter
        router = _TypeRouter()
        router.add(actuator.func_a)
        router.add(actuator.func_c)

        # Test routing for various types
        self.assertEqual(router(A()), ["func_a: A"])
        self.assertEqual(router(B()), ["func_a: B"])
        self.assertEqual(router(C()), ["func_c: C"])
        self.assertEqual(router(D()), ["func_c: D"])
        self.assertEqual(router(E()), [])
        self.assertListEqual(['func_a: A', 'func_a: B', 'func_c: C', 'func_c: D'], list(
            actuator.iter_actions()))

    def test_attempt_type_routing_with_typehints(self):

        # Define observe-decorated functions
        class MyActuator(Actuator):

            @attempt
            def func_a(self, e: A):
                return f"func_a: {type(e).__name__}"

            @attempt()
            def func_ab(self, e: A | B):
                return f"func_ab: {type(e).__name__}"

        actuator = MyActuator()

        # Initialize TypeRouter
        router = _TypeRouter()
        router.add(actuator.func_a)
        router.add(actuator.func_ab)

        # Test routing for various types
        self.assertEqual(router(A()), ["func_a: A", "func_ab: A"])
        # func_a will not be called because a function for B was found!
        self.assertEqual(router(B()), ["func_ab: B"])
        self.assertEqual(router(E()), [])

        self.assertListEqual(['func_a: A', 'func_ab: A', 'func_ab: B'], list(
            actuator.iter_actions()))


if __name__ == "__main__":
    unittest.main()
