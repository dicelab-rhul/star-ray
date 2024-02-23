# pylint: disable=no-member
import json

from typing import List
from importlib.resources import files
from dataclasses import asdict
from ray import serve
from jinja2 import Environment, FileSystemLoader, StrictUndefined

from star_ray.typing import Event
from star_ray.agent import Agent
from star_ray.agent.sensor import HistorySensor
from star_ray.plugin.xml import QueryXPath

from .webserver import WebServer, get_default_template_data

DEFAULT_WEBSERVER_PORT = 8888
DEFAULT_WEBSERVER_HOST = "localhost"
DEFAULT_SERVE_SETTINGS = dict(port=DEFAULT_WEBSERVER_PORT, host=DEFAULT_WEBSERVER_HOST)
_TEMPLATES_PATH = files(__package__).joinpath("static/templates")
_JINJA2_ENV = Environment(
    loader=FileSystemLoader(_TEMPLATES_PATH), undefined=StrictUndefined
)
DEFAULT_SVG_CODE = """<svg id="root" xmlns="http://www.w3.org/2000/svg"></svg>"""


class WebXMLAvatar(Agent):
    """
    A web-based agent designed for managing and serving XML/SVG content through via a web server.

    The agent initializes a Ray Serve application to serve the XML/SVG content, sets up a web socket for real-time communication, and listens for updates or changes to the XML/SVG, which are applied through the specified sensors and actuators.

    Methods:
        send(event: QueryXPath): Sends an update to the SVG based on the specified QueryXPath event. This method serializes the event as JSON and updates the web socket with the new SVG content or modifications.
        receive() -> List[Event]: Polls for and retrieves a list of events which represent user input from the web server.

    Example usage:
    ```
    sensors = [HistorySensor(index=..., whitelist_types=[QueryXPath])]
    actuators = [SomeActuator()]
    web_svg_avatar = WebSVGAvatar(sensors=sensors, actuators=actuators)
    ```
    """

    # name of the remote socket route
    _SVG_SOCKET_ROUTE_NAME = "svg_socket_route"
    _SVG_SOCKET_TEMPLATE_NAME = "svg_socket.html.jinja"

    def __init__(
        self,
        sensors,
        actuators,
        serve_kwargs=None,
        template_data=None,
        svg=None,
        **kwargs,
    ):
        """
        Initializes the `WebSVGAvatar` agent, setting up the web server, web socket communication, and initial SVG content.

        Parameters:
            sensors (`List[Sensor]`): A list of sensor instances for the agent to receive input data. Typically the `Event`s gathered by the agents sensors should be sent to the webserver via `send`.
            actuators (`List[Actuator]`): A list of actuator instances for the agent to perform actions. Typically these actions will be received from the webserve as user input (e.g. a `MouseButtonEvent`), these may be further processed by the agents actuators (or in the `__cycle__` method) and attempted.
            serve_kwargs (`Dict`, optional): Configuration options for the Ray Serve instance, including HTTP options such as port and host. Default is None, which uses default settings `{port=8888, host='localhost'}`.
            template_data (`Dict`, optional): Data to be passed into the web server template for rendering the initial HTML page. Includes placeholders for dynamic content that can be updated in real-time. Default is None, which fetches the default template data.
            svg (`str`, optional): The initial SVG code to be displayed and managed by the agent. Default is an empty SVG root element.

        """
        super().__init__(sensors, actuators, **kwargs)
        if serve_kwargs is None:
            serve_kwargs = dict(
                http_options=dict(port=DEFAULT_WEBSERVER_PORT, host="localhost")
            )
        serve.start(**serve_kwargs)
        self._socket_route = WebXMLAvatar._SVG_SOCKET_ROUTE_NAME
        if template_data is None:
            template_data = get_default_template_data()
        if svg is None:
            svg = DEFAULT_SVG_CODE
        port = serve_kwargs["http_options"]["port"]
        host = serve_kwargs["http_options"]["host"]
        template_data["svg_socket"] = dict(route=self._socket_route)
        # Need to pre-render the SVG socket script as it is being used as a template argument. The values will not be resolved otherwise!
        template_data["body"] += _JINJA2_ENV.get_template(
            WebXMLAvatar._SVG_SOCKET_TEMPLATE_NAME
        ).render(
            dict(
                address=f"{host}:{port}",
                route=self._socket_route,
                svg_code=svg,
            )
        )
        self._webserver = serve.run(WebServer.bind(template_data=template_data))
        self._webserver.add_web_socket_handler.remote(self._socket_route)

    def _send_dict(
        self, data: dict
    ) -> (
        None
    ):  # TODO a response is probably needed! we need to ensure that the update was successful!
        data = json.dumps(data)
        self._webserver.update_socket.remote(self._socket_route, data)

    def send(self, event: QueryXPath) -> None:
        """
        Sends an update to the XML/SVG based on the specified `QueryXPath` event. This method serializes the event as JSON and sends it through the web socket to apply changes to the XML/SVG content. The given event will typically have been retrieved from the sensors. A common pattern is make use of a `HistorySensor` to gather the most recent changes to the environment state, these changes will then be reflected in the web view.

        Parameters:
            event (QueryXPath): The event containing the QueryXPath command to update the XML/SVG content.
        """
        self._send_dict(asdict(event))

    def receive(self) -> List[Event]:
        """
        Retrieves a list of the most recent user inputs events from the web server. These events will typically be provided to the actuators in `__cycle__` for further processing.

        Returns:
            List[Event]: list of the most recent user input events.
        """
        return self._webserver.get_events.remote().result()
