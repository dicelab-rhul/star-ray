# pylint: disable=W0212
from types import EllipsisType
from datetime import datetime
from dataclasses import dataclass, astuple, asdict, field
from typing import List, Tuple, Type, Optional, Dict
from ast import literal_eval
from lxml import etree

from star_ray.event import Event, SelectResponse
from star_ray.environment.history._h5history import _HistoryH5Sync
from star_ray.environment.history._history import _History
from star_ray.agent import ActiveSensor

from .xml_change import XMLChangeTracker


__all__ = ("XMLHistory", "XMLHistorySensor", "QueryXMLHistory", "xml_history")


class XMLHistorySensor(ActiveSensor):

    def __sense__(self) -> List["QueryXMLHistory"]:
        return [QueryXMLHistory.new(self.id, index=...)]


@dataclass
class QueryXMLHistory(Event):

    index: int | slice | EllipsisType

    @staticmethod
    def new(
        source: str,
        index: slice | int | EllipsisType = ...,
    ) -> "QueryXMLHistory":
        return QueryXMLHistory(
            *astuple(Event.new(source)),
            index=index,
        )


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

    def notify(self, **kwargs: Dict[str, str]):
        self._history.push(kwargs)

    def _new_response(
        self,
        query_id: str,
        index: int | slice | EllipsisType,
        response_source: Optional[str] = None,
    ):
        return SelectResponse.new(
            response_source,
            query_id,
            success=True,
            data=self._history[index],
        )

    def _handle_ellipsis(
        self, query: QueryXMLHistory, response_source: Optional[str] = None
    ):
        assert query.index is ...
        qa = self._history_queried_at.get(query.source, 0)
        self._history_queried_at[query.source] = len(self._history)
        return self._new_response(
            query.id, slice(qa, None, None), response_source=response_source
        )

    def __select__(self, query: QueryXMLHistory, response_source: Optional[str] = None):
        if query.index is ...:
            return self._handle_ellipsis(query, response_source=response_source)
        else:
            return self._new_response(
                query.id, query.index, response_source=response_source
            )

    def close(self):
        self._history.close()


def xml_history(
    use_disk=True,
    path: str = None,
    buffer_size: int = 10000,
    flush_prop: float = 0.1,
    force_overwrite: bool = False,
):
    def _history(cls):
        original_init = cls.__init__

        def __init_wrapper(self, *args, parser=None, **kwargs):
            if parser is None:
                parser = etree.XMLParser()
            history = XMLHistory(
                use_disk=use_disk,
                path=path,
                buffer_size=buffer_size,
                flush_prop=flush_prop,
                force_overwrite=force_overwrite,
            )
            # this will update the parser to use a special tracking element.
            # history will have its `notify` method called whenever there is
            # a change to xml that is parsed by the given parser.
            # data structure to store the history, this can then be retrieved by using a QueryXMLChangeHistory select event!
            self._history = XMLChangeTracker.new(parser, history)
            original_init(self, *args, **kwargs, parser=parser)

        cls.__init__ = __init_wrapper

        original_select = cls.__select__

        def __select_wrapper(self, query):
            if not isinstance(query, QueryXMLHistory):
                return original_select(self, query)
            else:
                return self._history.__select__(query, response_source=self.id)

        cls.__select__ = __select_wrapper
        return cls

    return _history
