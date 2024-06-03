from star_ray.event import Action, ActiveObservation, ErrorActiveObservation
from star_ray.plugin.web import WebServer, SocketHandler
from star_ray import Ambient, Agent


import asyncio

from star_ray.pubsub import Subscribe, Unsubscribe


class AmbientStub(Ambient):

    def __init__(self):
        super().__init__([])

    def __select__(self, action: Action) -> ActiveObservation | ErrorActiveObservation:
        pass

    def __update__(self, action: Action) -> ActiveObservation | ErrorActiveObservation:
        pass

    def __subscribe__(
        self, action: Subscribe | Unsubscribe
    ) -> ActiveObservation | ErrorActiveObservation:
        pass


class MyAvatar(Agent, SocketHandler):

    def __cycle__(self):
        pass

    def send(self):
        return super().send()

    def receive(self, data):
        print(data)


server = WebServer(AmbientStub(), MyAvatar)
asyncio.run(server.run())
