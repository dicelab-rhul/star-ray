from typing import List, Type, Dict, Any
import itertools
from pydantic import BaseModel
from .serde import SocketSerde


def _get_name_dict(cls_dict):
    result = {}
    for key, value in cls_dict.items():
        name = key.split(".")[-1]
        if name in result:
            raise ValueError(f"Duplicate class name found: {name}")
        result[name] = value
    return result


def _fully_qualified_name(cls):
    return cls.__module__ + "." + cls.__qualname__


def _iter_subclasses(cls):
    for subclass in cls.__subclasses__():
        yield subclass
        yield from _iter_subclasses(subclass)


def _iter_class_names(event_types, recursive):
    yield from ((_fully_qualified_name(cls), cls) for cls in event_types)
    if recursive:
        subclasses = itertools.chain(*(_iter_subclasses(cls) for cls in event_types))
        yield from ((_fully_qualified_name(cls), cls) for cls in subclasses)


class SocketSerdePydantic(SocketSerde):
    """A [SocketSerde] implementation for Pydantic BaseModel serialization.
    This class uses the [SocketSerde.PROTOCOL_JSON] protocol and as such expects dictionary objects in `serialize` and `deserialize`.
    It uses a special field `event_type` to resolve the class to use then uses `pydantic`'s serialization mechanism. It assumes that all incoming events are instances of `pydantic` `BaseModel`.
    """

    def __init__(self, event_types: List[Type], recursive=False, fully_qualified=False):
        """
        Initialize the SocketSerdePydantic instance.

        Args:
            event_types (List[Type]): A list of Pydantic BaseModel subclasses which may be used in to serde events.
            recursive (bool): If True, include subclasses of [event_types] recursively.
            fully_qualified (bool): If True, use fully-qualified class names for serialization.

        Raises:
            TypeError: If any provided event type does not extend Pydantic `BaseModel`.
            ValueError: If no serializer is found for a given event type.
        """
        super().__init__(protocol_dtype=SocketSerde.PROTOCOL_JSON)
        # validate the classes, they must all extend pydantic BaseModel to enable serialisation
        for cls in event_types:
            if not issubclass(cls, BaseModel):
                raise TypeError(
                    f"Provided event type {cls} does is not a subclass of `pydantic.BaseModel`."
                )

        # contains a mapping cls_name -> cls
        cls_dict = dict(_iter_class_names(event_types, recursive))
        if not fully_qualified:
            cls_dict = _get_name_dict(cls_dict)
        self._cls_dict = cls_dict
        self._fully_qualified = fully_qualified

    def serialize(self, event: BaseModel) -> Dict[str, Any]:
        serialized = event.model_dump(mode="json")
        assert not "event_type" in serialized
        if self._fully_qualified:
            serialized["event_type"] = _fully_qualified_name(event.__class__)
        else:
            serialized["event_type"] = event.__class__.__qualname__
        return serialized

    def deserialize(self, event: Dict[str, Any]) -> Any:
        event_type = event.get("event_type", None)
        if not event_type:
            raise ValueError(
                f"Failed to deserialize {event}, required attribute `event_type` was not specified."
            )
        cls = self._cls_dict.get(event_type, None)
        if not cls:
            raise ValueError(
                f"Failed to deserialize {event}, no serializer was found for {event_type}"
            )
        return cls.model_validate(event)
