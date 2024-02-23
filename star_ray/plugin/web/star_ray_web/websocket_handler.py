import asyncio
from fastapi import WebSocket, WebSocketDisconnect

__all__ = ("WebSocketHandler",)


class WebSocketHandler:

    def __init__(self, route):
        super().__init__()
        self._route = route
        self._message = None
        self._changed = asyncio.Event()
        self._closed = asyncio.Event()

    def update(self, message):
        if self._closed.is_set():
            raise ValueError(
                "Attempted to send data to websocket '{self._route}', but it was closed, try reconnecting"
            )
        self._message = message
        self._changed.set()

    def close(self):
        self._closed.set()

    async def open(self, websocket: WebSocket, *args, **kwargs):
        await websocket.accept()
        try:
            while not self._closed.is_set():
                await self._changed.wait()
                self._changed.clear()
                await websocket.send_text(self._message)
            websocket.close()
        except WebSocketDisconnect:
            self._closed.set()
