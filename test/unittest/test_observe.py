import unittest
from star_ray.agent.component.type_routing import _TypeRouter, observe


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


class TestObserve(unittest.TestCase):

    def test_observe_type_routing(self):
        # Define observe-decorated functions
        @observe([A])
        def func_a(e):
            return f"func_a: {type(e).__name__}"

        @observe([C])
        def func_c(e):
            return f"func_c: {type(e).__name__}"

        # Initialize TypeRouter
        router = _TypeRouter()
        router.add(func_a)
        router.add(func_c)

        # Test routing for various types
        self.assertEqual(router(A()), ["func_a: A"])
        self.assertEqual(router(B()), ["func_a: B"])
        self.assertEqual(router(C()), ["func_c: C"])
        self.assertEqual(router(D()), ["func_c: D"])
        self.assertEqual(router(E()), [])

    def test_observe_type_routing_with_typehints(self):

        @observe
        def func_a(e: A):
            return f"func_a: {type(e).__name__}"

        @observe
        def func_ab(e: A | B):
            return f"func_ab: {type(e).__name__}"

        # Initialize TypeRouter
        router = _TypeRouter()
        router.add(func_a)
        router.add(func_ab)

        # Test routing for various types
        self.assertEqual(router(A()), ["func_a: A", "func_ab: A"])
        # func_a will not be called because a function for B was found!
        self.assertEqual(router(B()), ["func_ab: B"])
        self.assertEqual(router(E()), [])


if __name__ == "__main__":
    unittest.main()
