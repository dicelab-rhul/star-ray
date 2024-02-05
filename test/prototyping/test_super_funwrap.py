from functools import wraps


def _capture(f):
    @wraps(f)
    def wrapper(self, *args, **kwargs):
        print("wrapped")
        return f(self, *args, **kwargs)
        # ^ "f" is retrieved from the class in __init_subclass__, before being
        # bound, so "self" is forwarded explicitly

    return wrapper


class A:
    def __init_subclass__(cls, *args, **kw):
        super().__init_subclass__(*args, **kw)
        fnames = {
            "foo",
        }
        for name in fnames:
            if name not in cls.__dict__:
                continue
            setattr(cls, name, _capture(getattr(cls, name)))
            # ^no need to juggle with binding the captured method:
            # it will work just as any other method in the class, and
            # `self` will be filled in by the Python runtime itself.

            # \/ also, no need to return anything.


class B(A):
    def foo(self):
        pass


B().foo()
