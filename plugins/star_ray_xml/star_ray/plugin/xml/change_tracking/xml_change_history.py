# pylint: disable=W0212
from datetime import datetime
from typing import List, Dict
from ast import literal_eval
from pydantic import validator, computed_field
import types

from star_ray.event import Action, Observation, ActiveObservation
from star_ray.utils.history import _History, _HistoryH5Sync
from star_ray.utils import SliceType, EllipsisType

from .xml_change_tracking import xml_change_tracker, has_change_tracking
from ..utils import _LOGGER

__all__ = ("XMLHistory", "QueryXMLHistory", "xml_history")

# TODO this should probably be a passive sensor. We dont want to constantly be polling for new updates
# class XMLHistorySensor(Sensor):

#     def __sense__(self) -> List["QueryXMLHistory"]:
#         return [QueryXMLHistory(index=...)]


class QueryXMLHistory(Action):

    index_: int | SliceType | EllipsisType

    def __init__(self, index: int | slice | types.EllipsisType = None, **kwargs):
        super().__init__(index_=index, **kwargs)

    @validator("index_", pre=True, always=True)
    @classmethod
    def validate_index(cls, value):
        if isinstance(value, int):
            return value
        elif isinstance(value, slice):
            return SliceType(value.start, value.stop, value.step)
        elif isinstance(value, types.EllipsisType):
            return EllipsisType()
        else:
            raise ValueError(
                f"Invalid type: {type(value)} must be an index type (int, slice, Ellipsis)"
            )

    @computed_field()
    @property
    def index(self) -> int | slice | types.EllipsisType:
        if isinstance(self.index_, int):
            return self.index_
        else:
            return self.index_.get_value()

    class Config:
        arbitrary_types_allowed = True


class XMLHistory:

    def __init__(
        self,
        use_disk: bool = True,
        path: str = None,
        buffer_size: int = 10000,
        flush_prop: float = 0.1,
        force_overwrite: bool = False,
    ):
        super().__init__()
        # datastructure that records when history queries were last made given the source
        # this is used when the query index == ellipsis
        self._history_queried_at = {}
        self._history = None

        if use_disk:
            # set up serialization
            self._event_type_store = {}

            def serialize(obj):
                return str(obj).encode("UTF-8")

            def deserialize(obj):
                return literal_eval(obj)

            now = datetime.now()
            dt = now.strftime("%Y-%m-%d_%H-%M-%S")
            if path is None:
                path = f"./xml_change_history-{dt}.h5"
            self._history = _HistoryH5Sync(
                path=path,
                buffer_size=buffer_size,
                flush_proportion=flush_prop,
                force=force_overwrite,
                serialize=serialize,
                deserialize=deserialize,
            )

        else:  # dont use disk.. this is probably a bad idea if there are many events expected!
            self._history = _History()

    def notify(self, event: Dict):
        self._history.push(event)

    def _new_response(
        self,
        index: int | slice | EllipsisType,
        action: Action = None,
    ):
        if action:
            return ActiveObservation(
                action_id=action,
                values=self._history[index],
            )
        else:
            Observation(values=self._history[index])

    def _handle_ellipsis(self, query: QueryXMLHistory):
        assert query.index is ...
        qa = self._history_queried_at.get(query.source, 0)
        self._history_queried_at[query.source] = len(self._history)
        return self._new_response(slice(qa, None, None), action=query)

    def __select__(self, query: QueryXMLHistory):
        if query.index is ...:
            return self._handle_ellipsis(query)
        else:
            return self._new_response(query.index, action=query)

    def close(self):
        self._history.close()


def xml_history(
    use_disk: bool = True,
    path: str = None,
    buffer_size: int = 10000,
    flush_prop: float = 0.1,
    force_overwrite: bool = False,
):
    def _history(
        cls,
    ):
        if not has_change_tracking(cls):
            raise TypeError(
                "`xml_history` requires `change_tracking`, make use of the `@change_tracking` decorator."
            )

        class XMLHistoryTracker(cls):
            def __init__(self, *args, parser=None, **kwargs):
                self._history = XMLHistory(
                    use_disk=use_disk,
                    path=path,
                    buffer_size=buffer_size,
                    flush_prop=flush_prop,
                    force_overwrite=force_overwrite,
                )
                # TODO parser = XMLChangeTracker.new(self._history, parser=parser)
                super().__init__(*args, parser=parser, **kwargs)
                self.add_xml_change_callback(self.__notify_xml_change__)

            def __notify_xml_change__(self, event: Dict):
                self._history.notify(event)

            def __select__(self, event, *args, **kwargs):
                if not isinstance(event, QueryXMLHistory):
                    return super().__select__(event, *args, **kwargs)
                else:
                    return self._history.__select__(event)

        return XMLHistoryTracker

    return _history


# original_init = cls.__init__

# def __init_wrapper(self, *args, parser=None, **kwargs):
#     if parser is None:
#         parser = etree.XMLParser()
#     self._history = XMLHistory(
#         use_disk=use_disk,
#         path=path,
#         buffer_size=buffer_size,
#         flush_prop=flush_prop,
#         force_overwrite=force_overwrite,
#     )
#     # this will update the parser to use a special tracking element.
#     # history will have its `notify` method called whenever there is
#     # a change to xml that is parsed by the given parser.
#     # data structure to store the history, this can then be retrieved by using a QueryXMLChangeHistory select event!
#     parser = XMLChangeTracker.new(self._history, parser=parser)
#     original_init(self, *args, **kwargs, parser=parser)

# cls.__init__ = __init_wrapper

# original_select = cls.__select__

# def __select_wrapper(self, query):
#     if not isinstance(query, QueryXMLHistory):
#         return original_select(self, query)
#     else:
#         return self._history.__select__(query)

# cls.__select__ = __select_wrapper
# return cls
