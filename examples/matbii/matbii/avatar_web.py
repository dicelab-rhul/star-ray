from star_ray_web import WebSVGAvatar

from star_ray.agent.sensor import SensorHistory


class MATBIIAvatar(WebSVGAvatar):

    def __init__(self)

    def __cycle__(self):
        # update the color of the circle
        query = QueryXML.new("test", "circle", {"fill": self.random_color()})
        self.update(query)

        # update the color of both rects
        query = QueryXPath.new("test", "//svg:rect", {"fill": self.random_color()})
        self.update(query)

        # update the text in the text element
        query = QueryXPath.new(
            "test", "//svg:text/text()", str(random.randint(0, 10000))
        )
        self.update(query)

        actions = self._webserver.get_events.remote().result()
        # attempt each of the actions
        for action in actions:
            if isinstance(action, MouseButtonEvent):
                print(["DOWN", "UP", "CLICK"][action.status])

    def update(self, query):
        query = json.dumps(asdict(query))
        self._webserver.update_socket.remote(self._socket_route, query)
