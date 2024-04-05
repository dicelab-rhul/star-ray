from star_ray.plugin.web import SocketSerdePydantic

from star_ray.event import MouseButtonEvent


serde = SocketSerdePydantic(
    event_types=[MouseButtonEvent], recursive=True, fully_qualified=False
)

event = MouseButtonEvent(
    source=1, button=0, position=(10, 10), status=0, target=["mytarget"]
)

ser = serde.serialize(event)
de = serde.deserialize(ser)
print(ser)
print(de)
