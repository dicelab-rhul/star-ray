# # pylint: disable=W0212
# from types import EllipsisType
# from datetime import datetime
# from dataclasses import dataclass, astuple, asdict, field
# import json
# from typing import List, Tuple, Type, Optional

# from star_ray.event.responseevent import SelectResponse
# from ...event import Event

# from ._history import _History
# from ._h5history import _HistoryH5Sync


# @dataclass
# class QueryHistory(Event):

#     index: int | slice | EllipsisType
#     whitelist_types: Optional[Tuple[Type]] = None
#     blacklist_types: Optional[Tuple[Type]] = None

#     @staticmethod
#     def new(
#         source: str,
#         index: slice | int | EllipsisType = ...,
#         whitelist_types: Optional[List[Type] | Tuple[Type]] = None,
#         blacklist_types: Optional[List[Type] | Tuple[Type]] = None,
#     ):
#         return QueryHistory(
#             *astuple(Event.new(source)),
#             index=index,
#             whitelist_types=tuple(whitelist_types) if whitelist_types else None,
#             blacklist_types=tuple(blacklist_types) if blacklist_types else None,
#         )

#     def filter(self, queries):
#         if self.whitelist_types:
#             queries = [
#                 element
#                 for element in queries
#                 if isinstance(element, self.whitelist_types)
#             ]
#         if self.blacklist_types:
#             queries = [
#                 element
#                 for element in queries
#                 if not isinstance(element, self.blacklist_types)
#             ]
#         return queries


# class History:

#     def __init__(
#         self,
#         update: bool = True,
#         select: bool = False,
#         update_response: bool = False,
#         select_response: bool = False,
#         use_disk: bool = True,
#         path: str = None,
#         buffer_size: int = 10000,
#         flush_prop: float = 0.1,
#         force_overwrite: bool = False,
#     ):
#         super().__init__()

#         update = update or update_response
#         select = select or select_response
#         if not (update or select):
#             raise ValueError(
#                 "A history is being created with no option for recording events, both `update` and `select` cannot be `False`."
#             )

#         # datastructure that records when history queries were last made given the source
#         # this is used when the query index == ellipsis
#         self._history_queried_at = {}
#         self._history = None

#         if use_disk:
#             # set up serialization
#             self._event_type_store = {}

#             def serialize(obj):
#                 self._event_type_store[obj.__class__.__name__] = type(obj)
#                 data = dict(type=obj.__class__.__name__, data=asdict(obj))
#                 return json.dumps(data)

#             def deserialize(obj):
#                 data = json.loads(obj)
#                 return self._event_type_store[data["type"]](**data["data"])

#             now = datetime.now()
#             dt = now.strftime("%Y-%m-%d_%H-%M-%S")
#             if path is None:
#                 path = f"./event_store-{dt}.h5"
#             self._history = _HistoryH5Sync(
#                 path=path,
#                 buffer_size=buffer_size,
#                 flush_proportion=flush_prop,
#                 force=force_overwrite,
#                 serialize=serialize,
#                 deserialize=deserialize,
#             )

#         else:  # dont use disk.. this is probably a bad idea if there are many events expected!
#             self._history = _History()

#         self._push_update = (
#             self._push_with_response if update_response else self._push_without_response
#         )
#         self._push_select = (
#             self._push_with_response if select_response else self._push_without_response
#         )

#     def push_update(self, query, response):
#         self._push_update(query, response)

#     def push_select(self, query, response):
#         self._push_select(query, response)

#     def _push_with_response(self, query, response):
#         self._history.push(query)
#         self._history.push(response)

#     def _push_without_response(self, query, _):
#         self._history.push(query)

#     def _handle_ellipsis(self, query: QueryHistory):
#         assert query.index is ...
#         qa = self._history_queried_at.get(query.source, 0)
#         self._history_queried_at[query.source] = len(self._history)
#         return self._new_response(query, slice(qa, None, None))

#     def _new_response(self, query, index):
#         return SelectResponse.new(
#             "environment",  # TODO maybe use an id instead?
#             query,
#             success=True,
#             data=query.filter(self._history[index]),
#         )

#     def handle_history_query(self, query: QueryHistory):
#         if query.index is ...:
#             return self._handle_ellipsis(query)
#         else:
#             return self._new_response(query, query.index)

#     def close(self):
#         self._history.close()


# def history(
#     update=True,
#     select=False,
#     update_response=False,
#     select_response=False,
#     use_disk=True,
#     path: str = None,
#     buffer_size: int = 10000,
#     flush_prop: float = 0.1,
#     force_overwrite: bool = False,
# ):

#     def _history(cls):
#         original_init = cls.__init__

#         def __init_wrapper(self, *args, **kwargs):
#             original_init(self, *args, **kwargs)
#             # data structure to store the history
#             self._history = History(
#                 update_response=update_response,
#                 select_response=select_response,
#                 use_disk=use_disk,
#                 path=path,
#                 buffer_size=buffer_size,
#                 flush_prop=flush_prop,
#                 force_overwrite=force_overwrite,
#             )

#         cls.__init__ = __init_wrapper

#         if update:
#             original_update = cls.__update__

#             def __update_wrapper(self, query):
#                 response = original_update(self, query)
#                 self._history.push_update(query, response)
#                 return response

#             cls.__update__ = __update_wrapper

#         original_select = cls.__select__

#         if select:

#             def __select_wrapper(self, query):
#                 if not isinstance(query, QueryHistory):
#                     response = original_select(self, query)
#                     self._history.push_select(query, response)
#                     return response
#                 else:
#                     return self._history.handle_history_query(query)

#         else:

#             def __select_wrapper(self, query):
#                 if not isinstance(query, QueryHistory):
#                     return original_select(self, query)
#                 else:
#                     return self._history.handle_history_query(query)

#         cls.__select__ = __select_wrapper

#         return cls

#     return _history
