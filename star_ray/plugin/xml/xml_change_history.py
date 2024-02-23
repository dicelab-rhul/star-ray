# pylint: disable=W0212
from types import EllipsisType
from datetime import datetime
from dataclasses import dataclass, astuple, asdict, field
from typing import List, Tuple, Type, Optional
from ast import literal_eval
from lxml import etree
import re

from star_ray.event.responseevent import SelectResponse

from .xml_change import XMLChangeTracker
from ...event import Event
from ...environment.history._h5history import _HistoryH5Sync
from ...environment.history._history import _History


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

    def notify(self, **kwargs):
        self._history.push(kwargs)

    def _handle_ellipsis(self, query: QueryXMLHistory):
        assert query.index is ...
        qa = self._history_queried_at.get(query.source, 0)
        self._history_queried_at[query.source] = len(self._history)
        return self._new_response(query, slice(qa, None, None))

    def _new_response(self, query, index):
        print(self._history.buffer, index)
        return SelectResponse.new(
            "environment",  # TODO maybe use an id instead?
            query,
            success=True,
            data=self._history[index],
        )

    def handle_history_query(self, query: QueryXMLHistory):
        if query.index is ...:
            return self._handle_ellipsis(query)
        else:
            return self._new_response(query, query.index)

    def close(self):
        self._history.close()


def xml_history(
    use_disk=True,
    path: str = None,
    buffer_size: int = 10000,
    flush_prop: float = 0.1,
    force_overwrite: bool = False,
    # resolve_namespaces: bool = True,
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
                response = self._history.handle_history_query(query)
                # if resolve_namespaces:
                #     # get namespaces from the XML state...
                #     namespace_prefix = {v: k for k, v in self._state._namespaces}
                #     response.xpath = _replace_namespace_with_prefix(
                #         response.xpath, namespace_prefix
                #     )
                return response

        cls.__select__ = __select_wrapper
        return cls

    return _history
