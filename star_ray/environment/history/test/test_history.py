# pylint: disable=E1101,W0212

from star_ray.environment import history, QueryHistory, Ambient
from star_ray.event import Event
import unittest


class TestHistory(unittest.TestCase):

    def test_update_store(self):
        # Applying the history decorator with both update and select (and their responses) enabled
        @history(
            update=True,
            select=False,
            update_response=False,
            select_response=False,
            use_disk=True,
            buffer_size=10,
            flush_prop=0.5,
            force_overwrite=True,
        )
        class MockAmbient(Ambient):

            def __update__(self, query):
                return Event.new("UPDATE RESPONSE")

            def __select__(self, query):
                return Event.new("SELECT RESPONSE")

        ambient = MockAmbient([])
        test_events = []
        for i in range(10):
            query_update = Event.new(f"{i}")
            test_events.append(query_update)
            ambient.__update__(query_update)

        response = ambient.__select__(QueryHistory.new("me!"))
        self.assertListEqual(response.values, test_events)

        response = ambient.__select__(QueryHistory.new("me!"))
        # should be empty, because there were no updates since the last response
        self.assertListEqual(response.values, [])

        ambient.__select__(Event.new("SELECT!"))
        response = ambient.__select__(QueryHistory.new("me!"))
        # should still be empty since the "select" parameter was not given
        self.assertListEqual(response.values, [])

        test_events = []
        for i in range(5):
            query_update = Event.new(f"{i}")
            test_events.append(query_update)
            ambient.__update__(query_update)

        response = ambient.__select__(QueryHistory.new("me!"))
        # new events were added, see if they are retrieved
        self.assertListEqual(response.values, test_events)

    def test_select_store(self):
        # Applying the history decorator with both update and select (and their responses) enabled
        @history(
            update=True,
            select=True,
            update_response=False,
            select_response=False,
            use_disk=True,
            buffer_size=10,
            flush_prop=0.5,
            force_overwrite=True,
        )
        class MockAmbient(Ambient):

            def __update__(self, query):
                return Event.new("UPDATE RESPONSE")

            def __select__(self, query):
                return Event.new("SELECT RESPONSE")

        ambient = MockAmbient([])

        response = ambient.__select__(QueryHistory.new("me!"))
        # should be empty, because there were no queries so far
        self.assertListEqual(response.values, [])

        select_event = Event.new("SELECT!")
        update_event = Event.new("UPDATE!")
        ambient.__select__(select_event)
        ambient.__update__(update_event)
        response = ambient.__select__(QueryHistory.new("me!"))
        self.assertListEqual(response.values, [select_event, update_event])

        test_events = []
        for i in range(5):
            query_update = Event.new(f"{i}")
            test_events.append(query_update)
            ambient.__update__(query_update)

        response = ambient.__select__(QueryHistory.new("me!"))
        # new events were added, see if they are retrieved
        self.assertListEqual(response.values, test_events)

    def test_with_response(self):
        # Applying the history decorator with both update and select (and their responses) enabled
        @history(
            update=True,
            select=True,
            update_response=True,
            select_response=True,
            use_disk=True,
            buffer_size=10,
            flush_prop=0.5,
            force_overwrite=True,
        )
        class MockAmbient(Ambient):

            def __update__(self, query):
                return Event.new("UPDATE RESPONSE")

            def __select__(self, query):
                return Event.new("SELECT RESPONSE")

        ambient = MockAmbient([])

        response = ambient.__select__(QueryHistory.new("me!"))
        # should be empty, because there were no queries so far
        self.assertListEqual(response.values, [])

        select_event = Event.new("SELECT!")
        update_event = Event.new("UPDATE!")
        response_select = ambient.__select__(select_event)
        response_update = ambient.__update__(update_event)
        response = ambient.__select__(QueryHistory.new("me!"))
        self.assertListEqual(
            response.values,
            [select_event, response_select, update_event, response_update],
        )

        test_events = []
        for i in range(5):
            query_update = Event.new(f"{i}")
            test_events.append(query_update)
            response = ambient.__update__(query_update)
            test_events.append(response)

        response = ambient.__select__(QueryHistory.new("me!"))
        # new events were added, see if they are retrieved
        self.assertListEqual(response.values, test_events)
        print(response.values)


if __name__ == "__main__":
    unittest.main()
