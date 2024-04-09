def my_decorator(*_args, foo=None):
    if len(_args) == 1:
        func = _args[0]

        # If arguments are provided, return a decorator with arguments
        def wrapper(*args, **kwargs):
            print("Decorator without arguments")
            return func(*args, **kwargs)

        return wrapper
    else:
        # If no arguments are provided, return a decorator without arguments
        def _decorator(func):
            def wrapper(*args, **kwargs):
                print(f"Decorator with arguments, {foo}")
                return func(*args, **kwargs)

            return wrapper

        return _decorator


# Usage examples:
@my_decorator
def function1():
    print("Function 1")


@my_decorator(foo=1)
def function2():
    print("Function 2")


function1()  # Output: Decorator without arguments, Function 1
function2()  # Output: Decorator with arguments: ('arg1', 'arg2'), Function 2
