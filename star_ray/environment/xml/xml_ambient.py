from .xml_state import XMLState
from .query_xpath import QueryXPath
from ...environment.ambient import Ambient


class XMLAmbient(Ambient):
    def __init__(self, agents, xml, namespaces={}):
        super().__init__(agents)
        self.state = XMLState(xml, namespaces=namespaces)

    def __query__(self, query: QueryXPath):
        return self.state.__query__(query)
