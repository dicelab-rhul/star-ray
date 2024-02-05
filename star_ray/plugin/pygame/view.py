""" This package defines the PygameSVGEngine class. """
import pygame
import cairosvg
import numpy as np

from .event import (
    PYGAME_QUIT,
    PYGAME_KEYDOWN,
    PYGAME_KEYUP,
    PYGAME_MOUSEDOWN,
    PYGAME_MOUSEUP,
    PYGAME_MOUSEMOTION,
    _EventFactory,
)


class PygameView:
    def __init__(self, width=640, height=480, title=None):
        """
        Initializes the Pygame window.

        Args:
            width (int): Width of the window.
            height (int): Height of the window.
            title (str) : Title of the window.
        """
        pygame.init()  # pylint: disable=no-member
        self._width = width
        self._height = height
        self._screen = pygame.display.set_mode(self.size)
        self._surface = pygame.Surface(self.size)
        if title:
            pygame.display.set_caption(title)

    @property
    def size(self):
        return (self._width, self._height)

    @size.setter
    def size(self, value):
        self._width = value[0]
        self._height = value[1]
        self._surface = pygame.Surface(self.size)
        self._screen = pygame.display.set_mode(self.size)

    def surface_to_npim(self, surface):
        """Transforms a Cairo surface into a numpy array."""
        im = np.frombuffer(surface.get_data(), np.uint8)
        H, W = surface.get_height(), surface.get_width()
        im.shape = (H, W, 4)  # for RGBA
        # a copy must be made to avoid a seg fault if the backing array disappears... (not sure why this happens!)
        im = im[:, :, :3].transpose(1, 0, 2).copy()
        return im

    def svg_to_npim(self, svg_bytestring, dpi=100):
        """Renders a svg bytestring as a RGB image in a numpy array"""
        tree = cairosvg.parser.Tree(bytestring=svg_bytestring)
        surf = cairosvg.surface.PNGSurface(tree, None, dpi).cairo
        return self.surface_to_npim(surf)

    def render_svg(self, svg_code):
        array = self.svg_to_npim(svg_code)
        pygame.surfarray.blit_array(self._surface, array)
        self._screen.blit(self._surface, (0, 0))
        pygame.display.flip()

    def step(self):
        events = []
        for pg_event in pygame.event.get():
            if pg_event.type == PYGAME_QUIT:
                exit_event = _EventFactory.create_exit_event_from_pygame_event(pg_event)
                events.append(exit_event)
            elif pg_event.type in (PYGAME_KEYDOWN, PYGAME_KEYUP):
                key_event = _EventFactory.create_key_event_from_pygame_event(pg_event)
                events.append(key_event)
            elif pg_event.type in (PYGAME_MOUSEDOWN, PYGAME_MOUSEUP):
                mouse_button_event = (
                    _EventFactory.create_mouse_button_event_from_pygame_event(pg_event)
                )
                events.append(mouse_button_event)
            elif pg_event.type == PYGAME_MOUSEMOTION:
                mouse_motion_event = (
                    _EventFactory.create_mouse_motion_event_from_pygame_event(pg_event)
                )
                events.append(mouse_motion_event)
        return events

    def close(self):
        pygame.quit()  # pylint: disable=no-member
