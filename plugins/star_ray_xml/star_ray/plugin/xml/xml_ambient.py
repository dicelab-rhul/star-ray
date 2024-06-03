from typing import List, Dict, Any
from lxml import etree
from star_ray.environment.ambient import Ambient
from star_ray.event import ActiveObservation, ErrorActiveObservation
from star_ray.pubsub import Subscribe, Unsubscribe

from .xml_state import XMLState
from .query_xpath import QueryXPath


class XMLAmbient(Ambient):
    """An ambient implementation that uses XML as its underlying state representation and accepts actions derived from `QueryXPath`, to read and modify this state."""

    def __init__(
        self,
        agents: List[Any],
        xml: str,
        namespaces: Dict[str, str] = {},
        parser: etree.XMLParser = None,
    ):
        super().__init__(agents)
        if parser is None:
            parser = etree.XMLParser()
        self.state = XMLState(xml, namespaces=namespaces, parser=parser)

    def __select__(self, action: QueryXPath) -> ActiveObservation:
        return self.state.__select__(action)

    def __update__(self, action: QueryXPath) -> ActiveObservation:
        return self.state.__update__(action)

    def __subscribe__(
        self, action: Subscribe | Unsubscribe
    ) -> ActiveObservation | ErrorActiveObservation:
        pass
