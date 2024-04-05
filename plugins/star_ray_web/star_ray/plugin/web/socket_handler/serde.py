from abc import ABC, abstractmethod
from typing import ClassVar, Any
from fastapi import WebSocket


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


class SocketSerdeDict(SocketSerde):

    def __init__(self):
        super().__init__(protocol_dtype=SocketSerde.PROTOCOL_JSON)

    def serialize(self, event):
        return event

    def deserialize(self, event):
        return event


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
