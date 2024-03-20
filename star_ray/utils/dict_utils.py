from typing import Dict, Any


def merge_nested(d1: Dict[Any, Any], d2: Dict[Any, Any]) -> Dict[Any, Any]:
    """
    Recursively merges two nested dictionaries. Only merges the leaves from d2 into d1.
    Args:
        d1 (dict): The target dictionary into which `d2` is merged. This dictionary is modified in place.
        d2 (dict): The source dictionary from which key-value pairs are taken. `d2` remains unmodified.

    Returns:
        dict: The updated dictionary `d1` after merging in `d2`. Note that `d1` is modified in place, but also returned for convenience.

    Example:
        ```
        dict1 = {'a': 1, 'b': {'x': 2, 'y': 3}}
        dict2 = {'b': {'y': 4, 'z': 5}, 'c': 3, 'd': {'e': 6}}
        merged_dict = merge_nested_dicts(dict1, dict2)
        print(merged_dict)
        {'a': 1, 'b': {'x': 2, 'y': 4, 'z': 5}, 'c': 3, 'd': {'e': 6}}
        ```

    """
    for key in d2:
        if key in d1:
            if isinstance(d1[key], dict) and isinstance(d2[key], dict):
                merge_nested(d1[key], d2[key])
            else:
                # If the key exists in both but is not a dict in either,
                # or it's a dict in one but not the other, d2's value takes precedence.
                d1[key] = d2[key]
        else:
            # If the key is not in d1, add it from d2.
            d1[key] = d2[key]
    return d1
