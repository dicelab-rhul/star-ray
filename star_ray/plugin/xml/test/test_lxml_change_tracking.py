import unittest

from lxml import etree
from star_ray.plugin.xml import (
    QueryXPath,
    QueryXMLHistory,
    XMLAmbient,
    xml_history,
)

NAMESPACES = {"svg": "http://www.w3.org/2000/svg"}

XML = """
<svg width="200" height="200" xmlns="http://www.w3.org/2000/svg">
    <g>
        <!-- Circle 1 -->
        <circle cx="50" cy="50" r="30" fill="red" />
        <!-- Circle 2 -->
        <circle cx="150" cy="50" r="30" fill="green" />
    </g>
        <!-- Rectangle 1 -->
        <rect x="130" y="20" width="50" height="30" fill="orange" />
</svg>
"""


class TestXMLChangeHistory(unittest.TestCase):

    def test_update_store(self):
        # Applying the history decorator with both update and select (and their responses) enabled

        @xml_history(force_overwrite=True)
        class MyXMLAmbient(XMLAmbient):
            pass

        ambient = MyXMLAmbient([], xml=XML, namespaces=NAMESPACES)
        query = QueryXPath.new(
            "test", xpath="//svg:circle", attributes={"cx": 10, "cy": 10}
        )
        response = ambient.__update__(query)
        print(response)

        query = QueryXMLHistory.new("test")

        response = ambient.__select__(query)

        print(response)

    # def test_select_store(self):
    #     # Applying the history decorator with both update and select (and their responses) enabled
    #     @history(
    #         update=True,
    #         select=True,
    #         update_response=False,
    #         select_response=False,
    #         use_disk=True,
    #         buffer_size=10,
    #         flush_prop=0.5,
    #         force_overwrite=True,
    #     )
    #     class MockAmbient(Ambient):

    #         def __update__(self, query):
    #             return Event.new("UPDATE RESPONSE")

    #         def __select__(self, query):
    #             return Event.new("SELECT RESPONSE")

    #     ambient = MockAmbient([])

    #     response = ambient.__select__(QueryHistory.new("me!"))
    #     # should be empty, because there were no queries so far
    #     self.assertListEqual(response.values, [])

    #     select_event = Event.new("SELECT!")
    #     update_event = Event.new("UPDATE!")
    #     ambient.__select__(select_event)
    #     ambient.__update__(update_event)
    #     response = ambient.__select__(QueryHistory.new("me!"))
    #     self.assertListEqual(response.values, [select_event, update_event])

    #     test_events = []
    #     for i in range(5):
    #         query_update = Event.new(f"{i}")
    #         test_events.append(query_update)
    #         ambient.__update__(query_update)

    #     response = ambient.__select__(QueryHistory.new("me!"))
    #     # new events were added, see if they are retrieved
    #     self.assertListEqual(response.values, test_events)

    # def test_with_response(self):
    #     # Applying the history decorator with both update and select (and their responses) enabled
    #     @history(
    #         update=True,
    #         select=True,
    #         update_response=True,
    #         select_response=True,
    #         use_disk=True,
    #         buffer_size=10,
    #         flush_prop=0.5,
    #         force_overwrite=True,
    #     )
    #     class MockAmbient(Ambient):

    #         def __update__(self, query):
    #             return Event.new("UPDATE RESPONSE")

    #         def __select__(self, query):
    #             return Event.new("SELECT RESPONSE")

    #     ambient = MockAmbient([])

    #     response = ambient.__select__(QueryHistory.new("me!"))
    #     # should be empty, because there were no queries so far
    #     self.assertListEqual(response.values, [])

    #     select_event = Event.new("SELECT!")
    #     update_event = Event.new("UPDATE!")
    #     response_select = ambient.__select__(select_event)
    #     response_update = ambient.__update__(update_event)
    #     response = ambient.__select__(QueryHistory.new("me!"))
    #     self.assertListEqual(
    #         response.values,
    #         [select_event, response_select, update_event, response_update],
    #     )

    #     test_events = []
    #     for i in range(5):
    #         query_update = Event.new(f"{i}")
    #         test_events.append(query_update)
    #         response = ambient.__update__(query_update)
    #         test_events.append(response)

    #     response = ambient.__select__(QueryHistory.new("me!"))
    #     # new events were added, see if they are retrieved
    #     self.assertListEqual(response.values, test_events)
    #     print(response.values)


if __name__ == "__main__":
    unittest.main()
