"""Module implements UUID functionality that is used internally to generate unique ids for various objects (including events, agents and ambients)."""

import time
import random
import uuid


def int64_uuid() -> int:
    timestamp = int(time.time() * 1000)  # Convert current time to milliseconds
    rand_number = random.getrandbits(32)  # Generate a 32-bit random number
    unique_id = (timestamp << 32) | rand_number  # Combine timestamp and random number
    unique_id &= 0xFFFFFFFFFFFFFFFF  # Ensure the result is a 64-bit unsigned integer
    return unique_id


def str_uuid4() -> str:
    return str(uuid.uuid4())


__all__ = ("int64_uuid", "str_uuid4")
