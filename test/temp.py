import inspect
import types


def decorator(cls):
    original_init = cls.__init__

    # Define the new __init__ method
    def new_init(self, *args, **kwargs):
        print("Decorator added functionality before calling __init__")
        original_init(self, *args, **kwargs)
        print("Decorator added functionality after calling __init__")

    # Replace __init__ method with the new one
    cls.__init__ = types.MethodType(new_init, cls)
    return cls


@decorator
class MyClass:
    def __init__(self, x):
        self.x = x
        print("Original __init__ called")

    def method(self):
        print("Method called")


# Get the __init__ method using inspect
init_method = inspect.getattr_static(MyClass, "__init__")

# Check if the obtained attribute is a method
print(inspect.ismethod(init_method))  # Output: True

# Instantiate the decorated class
obj = MyClass(10)
