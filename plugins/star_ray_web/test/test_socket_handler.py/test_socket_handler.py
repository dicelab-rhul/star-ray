import asyncio
import uvicorn
import json
from fastapi import FastAPI, WebSocket
from websockets import connect
from star_ray.plugin.web import SocketHandler, SocketSerdePydantic
from star_ray import Event


class MyEvent(Event):
    foo: str


class MySocketHandler(SocketHandler):

    async def send(self):
        await asyncio.sleep(10)

    async def receive(self, data):
        print("RECEIVE: ", data)


app = FastAPI()


class WebSocketTest:
    def __init__(self, host="localhost", port=8000):
        self.host = host
        self.port = port
        self.server_url = f"ws://{host}:{port}"
        self.client = None
        self._serde = SocketSerdePydantic([MyEvent])
        self.socket_handler = MySocketHandler(serde=self._serde)
        app.websocket("/")(self.websocket_endpoint)

    async def websocket_endpoint(self, websocket: WebSocket):
        await self.socket_handler.serve(websocket)

    async def start_client(self):
        await asyncio.sleep(0.1)  # wait for server to start
        async with connect(self.server_url) as websocket:
            self.client = websocket
            event = MyEvent(source=1, foo="hello")
            await self.client.send(json.dumps(self._serde.serialize(event)))

    async def run_test(self):
        config = uvicorn.Config(
            app=app, host=self.host, port=self.port, log_level="info"
        )
        server = uvicorn.Server(config)
        client_task = asyncio.create_task(self.start_client())
        _, pending = await asyncio.wait(
            [server.serve(), client_task], return_when=asyncio.FIRST_COMPLETED
        )
        for task in pending:
            task.cancel()
        await server.shutdown()


async def run_test():
    test = WebSocketTest()
    await test.run_test()


asyncio.run(run_test())
