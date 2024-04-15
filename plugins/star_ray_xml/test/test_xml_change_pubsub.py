from star_ray.plugin.xml import (
    XMLAmbient,
    xml_change_tracker,
    xml_change_publisher,
    SubscribeXMLElementChange,
    UnsubscribeXMLElementChange,
    SubscribeXMLChange,
    UnsubscribeXMLChange,
    QueryXML,
)
from star_ray import Sensor
from star_ray.environment import _State
from pprint import pprint

NAMESPACES = {"svg": "http://www.w3.org/2000/svg"}

XML = """
<svg width="200" height="200" xmlns="http://www.w3.org/2000/svg">
    <g>
        <!-- Circle 1 -->
        <circle id="c1" cx="50" cy="50" r="30" fill="red" />
        <!-- Circle 2 -->
        <circle id="c2" cx="150" cy="50" r="30" fill="green" />
    </g>
        <!-- Rectangle 1 -->
        <rect x="130" y="20" width="50" height="30" fill="orange" />
</svg>
"""


@xml_change_publisher
@xml_change_tracker
class MyXMLAmbient(XMLAmbient):
    pass


class MySensor(Sensor):

    def __sense__(self):
        return [
            SubscribeXMLElementChange(topic="c1", subscriber=self),
            SubscribeXMLChange(topic="*", subscriber=self),
        ]


state = MyXMLAmbient([], xml=XML, namespaces=NAMESPACES)
sensor = MySensor()
sensor.__query__(_State.new(state))

state.__update__(QueryXML(element_id="c1", attributes={"x": 10}))

pprint(list(sensor.iter_observations()))
