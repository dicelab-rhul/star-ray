""" star-ray (Simulation Test-bed for Agent Research)-ray package."""

from .utils import logging

from .plugin import xml as xml_plugin

xml = xml_plugin

__all__ = ("xml",)
