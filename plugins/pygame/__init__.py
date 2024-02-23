import os

os.environ["PYGAME_HIDE_SUPPORT_PROMPT"] = "1"
from .view import PygameView
from .avatar import SVGAvatar

__all__ = ("PygameView", "SVGAvatar")
