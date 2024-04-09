from abc import ABC, abstractmethod
from typing import ClassVar, Any, ByteString
from fastapi import WebSocket
import json


class SocketSerde(ABC):

    PROTOCOL_JSON: ClassVar[str] = "json"
    PROTOCOL_BYTES: ClassVar[str] = "bytes"
    PROTOCOL_TEXT: ClassVar[str] = "text"

    def __init__(self, protocol_dtype, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.protocol_dtype = protocol_dtype

    @abstractmethod
    def serialize(self, event: Any):
        pass

    @abstractmethod
    def deserialize(self, event: Any):
        pass


class SocketSerdeRaw(SocketSerde):

    def __init__(self, protocol_dtype):
        super().__init__(protocol_dtype=protocol_dtype)

    def serialize(self, event):
        return event

    def deserialize(self, event):
        return event


class SocketSerdeDict(SocketSerdeRaw):

    def __init__(self):
        super().__init__(protocol_dtype=SocketSerde.PROTOCOL_JSON)

    def deserialize(self, event):
        _validate(event, dict, "JSON")
        return event

    def serialize(self, event):
        _validate(event, dict, "JSON")
        return event


class SocketSerdeText(SocketSerdeRaw):

    def __init__(self):
        super().__init__(protocol_dtype=SocketSerde.PROTOCOL_TEXT)

    def deserialize(self, event):
        _validate(event, str, "TEXT")
        return event

    def serialize(self, event):
        _validate(event, str, "TEXT")
        return event


class SocketSerdeBytes(SocketSerdeRaw):

    def __init__(self):
        super().__init__(protocol_dtype=SocketSerde.PROTOCOL_BYTES)

    def deserialize(self, event):
        _validate(event, bytes, "BYTES")
        return event

    def serialize(self, event):
        _validate(event, bytes, "BYTES")
        return event


def _validate(event, types, protocol):
    if not isinstance(event, (types)):
        raise TypeError(
            f"Receive invalid type: {type(event)}, expected `{types}` type when using protocol {protocol}."
        )


def _get_protocol_funcs(serde):
    async def receive_text(websocket: WebSocket):
        return await websocket.receive_text()

    async def receive_bytes(websocket: WebSocket):
        return await websocket.receive_bytes()

    async def receive_json(websocket: WebSocket):
        return await websocket.receive_json()

    async def send_text(websocket: WebSocket, data: Any):
        await websocket.send_text(data)

    async def send_bytes(websocket: WebSocket, data: Any):
        await websocket.send_bytes(data)

    async def send_json(websocket: WebSocket, data: Any):
        await websocket.send_json(data)

    dtype_receive_map = {
        SocketSerde.PROTOCOL_JSON: receive_json,
        SocketSerde.PROTOCOL_BYTES: receive_bytes,
        SocketSerde.PROTOCOL_TEXT: receive_text,
    }

    dtype_send_map = {
        SocketSerde.PROTOCOL_JSON: send_json,
        SocketSerde.PROTOCOL_BYTES: send_bytes,
        SocketSerde.PROTOCOL_TEXT: send_text,
    }

    assert serde.protocol_dtype in dtype_receive_map
    assert serde.protocol_dtype in dtype_send_map

    _send = dtype_send_map[serde.protocol_dtype]
    _receive = dtype_receive_map[serde.protocol_dtype]

    return _send, _receive
