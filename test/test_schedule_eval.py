import ast
import random
import inspect
from typing import Callable, List, Union

# List of allowed functions for timestamp expressions
ALLOWED_FUNCTIONS = {
    "uniform": random.uniform,
}


class SafeEvalVisitor(ast.NodeVisitor):

    def visit_BinOp(self, node: ast.BinOp) -> Union[float, int]:
        """Handle binary operations (+, -, *, /)."""
        left = self.visit(node.left)
        right = self.visit(node.right)

        if isinstance(node.op, ast.Add):
            return left + right
        elif isinstance(node.op, ast.Sub):
            return left - right
        elif isinstance(node.op, ast.Mult):
            return left * right
        elif isinstance(node.op, ast.Div):
            return left / right
        else:
            raise ValueError("Unsupported binary operator")

    def visit_Call(self, node: ast.Call) -> Callable:
        """Prepare a function call as a Callable for later execution."""
        if not isinstance(node.func, ast.Name):
            raise ValueError("Unsafe function call")
        func_name = node.func.id
        if func_name not in ALLOWED_FUNCTIONS:
            raise ValueError(f"Function {func_name} is not allowed")

        func = ALLOWED_FUNCTIONS[func_name]
        args = [self.visit(arg) for arg in node.args]

        # Validate the arguments against the function's signature
        try:
            sig = inspect.signature(func)
            sig.bind(*args)
        except TypeError as e:
            error_msg = (
                f"Argument mismatch for function '{func_name}': {e}\n"
                f"Expected signature: {sig}\n"
                f"Provided arguments: {[arg for arg in args]}"
            )
            raise ValueError(error_msg) from e

        # Return a Callable that, when called, will execute the function with the provided arguments
        return lambda: func(*args)

    def visit_Num(self, node: ast.Constant) -> float:
        """Return number directly."""
        return node.n

    def visit_Str(self, node: ast.Constant) -> str:
        """Return string directly."""
        return node.s

    def visit_Expr(self, node: ast.Expr) -> Callable:
        """Visit an expression."""
        return self.visit(node.value)

    def generic_visit(self, node: ast.AST) -> None:
        """Restrict to safe AST nodes."""
        raise ValueError("Unsupported expression")


def safe_eval(expr: str) -> List[Callable]:
    """
    Safely parse an expression to return a list of Callables for later execution.
    """
    tree = ast.parse(expr, mode="eval")
    result = SafeEvalVisitor().visit(tree.body)
    # Ensure the result is wrapped in a list if it's not already a list
    return [result] if not isinstance(result, list) else result


# Example usage
expressions = ["uniform(0, 1, 2)", "0.5 + 1", "'a string representing a timestamp'"]

for expr in expressions:
    result = safe_eval(expr)
    for callable_item in result:
        if callable(callable_item):
            print(f"Deferred execution for {expr}: {callable_item()}")
        else:
            print(f"Direct value for {expr}: {callable_item}")
