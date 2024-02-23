import uuid

__all__ = ("new_uuid",)


def new_uuid() -> str:
    """Generates a new uuid4.

    Returns:
        str: uuid
    """
    return str(uuid.uuid4())
