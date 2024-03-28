import re
from typing import Callable, List, Union
from random import uniform

from ast import literal_eval


# Mock actions for demonstration
def action1(arg):
    print(f"Executing action1 with arg: {arg}")


def action2(arg):
    print(f"Executing action2 with arg: {arg}")


def parse_schedule(schedule_str: str):
    # Regular expression to match the action lines
    action_line_re = re.compile(r"(\w+)\((.*?)\) @(\[.*?\]|<.*?>)")

    # Find all matches in the schedule string
    matches = action_line_re.findall(schedule_str)

    # Process each match
    for action_name, arg, timestamp_expr in matches:
        # Clean up timestamp expression
        timestamp_expr = timestamp_expr.strip("[]<>")

        # Schedule the action(s)
        for timestamp in timestamps:
            schedule_action(action_name, arg, timestamp)


# Function to "schedule" an action (for demonstration, it just prints the action)
def schedule_action(action_name: str, arg: str, timestamp: Union[float, Callable]):
    # Mock scheduling (direct execution here for demonstration)
    print(f"Scheduled {action_name} with arg '{arg}' at timestamp {timestamp}")
    globals()[action_name](arg)  # Execute the action (unsafe, for demonstration only)


# Example usage
schedule_str = """
action1('arg1') @[uniform(0,1), 0.5]
action2('arg2') @uniform(0,1)
"""

parse_schedule(schedule_str)
