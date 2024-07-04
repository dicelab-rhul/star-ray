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


class TestTypeRouting(unittest.TestCase):

    def test_type_routing(self):
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


if __name__ == "__main__":
    unittest.main()
