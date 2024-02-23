def test(var=1):
    class Foo:
        _var = var

        def __call__(self):
            return Foo._var

    return Foo()


x = test(var=1)
y = test(var=2)

print(x(), y())

print(type(x), type(y))
