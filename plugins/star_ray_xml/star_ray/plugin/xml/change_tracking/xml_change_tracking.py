""" TODO """

from typing import Callable, Dict
from lxml import etree
from .xml_tracking_element import _TrackingElement
from ..utils import _LOGGER

__all__ = ("xml_change_tracker",)


def has_change_tracking(cls):
    return hasattr(cls, "_xml_change_tracking") or any(
        [hasattr(cls, "_xml_change_tracking") for c in cls.__bases__]
    )


def xml_change_tracker(cls):
    if has_change_tracking(cls):
        raise TypeError(
            f"{cls} already implements change tracking, was this decorator applied more than once?",
        )

    class XMLChangeTracker(cls):
        _xml_change_tracking = True

        def __init__(self, *args, parser=None, xml_change_callbacks=None, **kwargs):
            parser = _new(self.notify, parser)
            self._xml_change_callbacks = set()
            if not xml_change_callbacks is None:
                for callback in xml_change_callbacks:
                    self._xml_change_callbacks.add(callback)
            super().__init__(*args, parser=parser, **kwargs)

        def notify(self, event: Dict):
            for callback in self._xml_change_callbacks:
                callback(event)

        def remove_xml_change_callback(self, callback: Callable):
            self._xml_change_callbacks.discard(callback)

        def add_xml_change_callback(self, callback: Callable):
            self._xml_change_callbacks.add(callback)

    return XMLChangeTracker


def _new(notify: Callable, parser: etree.XMLParser = None):
    if parser is None:
        parser = etree.XMLParser()

    class TrackingElement(_TrackingElement):
        def notify(self, **kwargs):
            return notify(kwargs)

    parser_lookup = etree.ElementDefaultClassLookup(element=TrackingElement)
    parser.set_element_class_lookup(parser_lookup)
    return parser


# def _ensure_notify_method(cls):
#     """Decorator to ensure a class has a notify method with the correct signature."""
#     # Check if 'notify' method exists
#     notify_method = next(
#         (m for n, m in inspect.getmembers(cls, inspect.isfunction) if n == "notify"),
#         None,
#     )

#     if notify_method is None:
#         raise TypeError(
#             f"{cls.__name__} must implement the method 'notify(self, event: Dict)'"
#         )

#     # Check the signature
#     expected_signature = inspect.Signature(
#         parameters=[
#             inspect.Parameter("self", inspect.Parameter.POSITIONAL_OR_KEYWORD),
#             inspect.Parameter(
#                 "event", inspect.Parameter.POSITIONAL_OR_KEYWORD, annotation=Dict
#             ),
#         ]
#     )

#     actual_signature = inspect.signature(notify_method)
#     if actual_signature != expected_signature:
#         raise TypeError(
#             f"{cls.__name__}.notify method must have signature 'notify(self, event: Dict)'"
#         )
