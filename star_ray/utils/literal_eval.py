from ast import (
    Constant,
    List,
    Tuple,
    Name,
    Starred,
    Dict,
    BinOp,
    Expression,
    Add,
    Sub,
    Mult,
    Div,
    Call,
    Set,
    parse,
    literal_eval,
)


def literal_eval_with_ops(node_or_string):
    """
    Safely evaluate an expression node or a string containing a Python
    expression. The string or node provided may only consist of the
    following Python literal structures: strings, bytes, numbers,
    tuples, lists, dicts, sets, booleans, None, and basic binary operations.

    Caution: A complex expression can overflow the C stack and cause a crash.
    """

    def _raise_malformed_node(node):
        msg = "malformed node or string"
        if lno := getattr(node, "lineno", None):
            msg += f" on line {lno}"
        raise ValueError(msg + f": {node!r}")

    def _convert(node):
        if isinstance(node, Constant):
            return node.value
        elif isinstance(node, Tuple):
            return tuple(map(_convert, node.elts))
        elif isinstance(node, List):
            # Handle list with unpacking
            result = []
            for elt in node.elts:
                if isinstance(elt, Starred):  # Unpacking operator
                    result.extend(_convert(elt.value))
                else:
                    result.append(_convert(elt))
            return result
        elif isinstance(node, Set):
            return set(map(_convert, node.elts))
        elif (
            isinstance(node, Call)
            and isinstance(node.func, Name)
            and node.func.id == "set"
            and node.args == node.keywords == []
        ):
            return set()
        elif isinstance(node, Dict):
            if len(node.keys) != len(node.values):
                _raise_malformed_node(node)
            return dict(zip(map(_convert, node.keys), map(_convert, node.values)))
        elif isinstance(node, BinOp):  # Handle binary operations
            left = _convert(node.left)
            right = _convert(node.right)
            if isinstance(node.op, Add):
                return left + right
            elif isinstance(node.op, Sub):
                return left - right
            elif isinstance(node.op, Mult):
                return left * right
            elif isinstance(node.op, Div):
                return left / right
            else:
                _raise_malformed_node(node)
        else:
            _raise_malformed_node(node)

    try:
        if isinstance(node_or_string, str):
            node_or_string = parse(node_or_string.lstrip(" \t"), mode="eval")
        if isinstance(node_or_string, Expression):
            node_or_string = node_or_string.body
    except SyntaxError:
        _raise_malformed_node(node_or_string)

    return _convert(node_or_string)
