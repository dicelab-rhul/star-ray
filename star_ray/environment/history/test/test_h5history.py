from star_ray.environment.history import _HistoryH5Sync
import unittest
import json
from dataclasses import dataclass, asdict


def compare(self, wrapper, test, N):
    for i in range(N):
        self.assertEqual(wrapper[i], test[i])
        self.assertEqual(wrapper[-(i + 1)], test[-(i + 1)])
        self.assertListEqual(wrapper[:i], test[:i])
        self.assertListEqual(wrapper[i:], test[i:])
        self.assertListEqual(wrapper[: -(i + 1)], test[: -(i + 1)])
        self.assertListEqual(wrapper[-(i + 1) :], test[-(i + 1) :])
        self.assertListEqual(wrapper[10:i], test[10:i])
        self.assertListEqual(wrapper[i : -(i + 1)], test[i : -(i + 1)])
    self.assertListEqual(wrapper[...], test[:])


class Test_HistoryH5Sync(unittest.TestCase):

    def test_disk(self):
        N = 30
        wrapper = _HistoryH5Sync(buffer_size=10, flush_proportion=0.5, force=True)
        test = []
        for i in range(N):
            wrapper.push(f"{i}")
            test.append(f"{i}")
        self.assertEqual(len(wrapper), N)
        compare(self, wrapper, test, N)

        wrapper.close()

    def test_seralized_dict(self):
        N = 30

        def serialize(obj):
            return json.dumps(obj).encode("UTF-8")

        def deserialize(obj):
            return json.loads(obj)

        wrapper = _HistoryH5Sync(
            buffer_size=10,
            flush_proportion=0.5,
            force=True,
            serialize=serialize,
            deserialize=deserialize,
        )
        test = []
        for i in range(N):
            wrapper.push({f"{i}": i})
            test.append({f"{i}": i})
        self.assertEqual(len(wrapper), N)
        compare(self, wrapper, test, N)
        wrapper.close()

    def test_seralized_dataclass(self):
        N = 30

        CLASS_STORE = {}

        def serialize(obj):
            CLASS_STORE[obj.__class__.__name__] = type(obj)
            data = dict(type=obj.__class__.__name__, data=asdict(obj))
            return json.dumps(data)

        def deserialize(obj):
            data = json.loads(obj)
            return CLASS_STORE[data["type"]](**data["data"])

        @dataclass
        class DataClass:
            x: int

        wrapper = _HistoryH5Sync(
            buffer_size=10,
            flush_proportion=0.5,
            force=True,
            serialize=serialize,
            deserialize=deserialize,
        )
        test = []
        for i in range(N):
            wrapper.push(DataClass(i))
            test.append(DataClass(i))
        self.assertEqual(len(wrapper), N)
        compare(self, wrapper, test, N)
        wrapper.close()


if __name__ == "__main__":
    unittest.main()
