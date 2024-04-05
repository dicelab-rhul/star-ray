import asyncio
from typing import Any
from abc import ABC, abstractmethod
from fastapi import WebSocket, WebSocketDisconnect
from .serde import SocketSerde, SocketSerdeDict, _get_protocol_funcs


class SocketHandler(ABC):

    def __init__(self, *args, serde: SocketSerde = None, **kwargs):
        super().__init__(*args, **kwargs)
        if serde is None:
            # use dictionary data as the default. `WebSocket.send_json` will automatically convert objects to json (i.e. their dictionary format)
            serde = SocketSerdeDict()
        self.serde = serde
        self.__websocket_send, self.__websocket_receive = _get_protocol_funcs(
            self.serde
        )
        self._send_task, self._receive_task = None, None
        self._websocket: WebSocket = None

    async def __receive__(self, websocket: WebSocket):
        try:
            while True:
                data = await self.__websocket_receive(websocket)
                data = self.serde.deserialize(data)
                await self.receive(data)
        except WebSocketDisconnect:
            pass

    async def __send__(self, websocket: WebSocket):
        try:
            while True:
                data = await self.send()
                data = self.serde.serialize(data)
                await self.__websocket_send(websocket, data)
        except WebSocketDisconnect:
            pass

    async def serve(self, websocket: WebSocket):
        if self._websocket:
            raise ValueError("WebsocketHandler is already connected.")
        self._websocket = websocket
        await websocket.accept()
        # Task for receiving data
        self._receive_task = asyncio.create_task(self.__receive__(websocket))
        # Task for sending data
        self._send_task = asyncio.create_task(self.__send__(websocket))
        # Wait for either task to finish (e.g., due to WebSocketDisconnect)
        _, pending = await asyncio.wait(
            [self._receive_task, self._send_task], return_when=asyncio.FIRST_COMPLETED
        )
        for task in pending:
            task.cancel()

    async def close(self):
        if self._websocket:
            # TODO the socket might already be closed, perhaps catch an exception here.
            await self._websocket.close()
        for task in [self._receive_task, self._send_task]:
            if task:
                task.cancel()

    @abstractmethod
    async def send(self) -> Any:
        pass

    @abstractmethod
    async def receive(self, data: Any) -> None:
        pass
