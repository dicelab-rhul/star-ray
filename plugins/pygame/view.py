""" This package defines the PygameSVGEngine class. """

import pygame
import cairosvg
import numpy as np
from lxml import etree as ET
import math

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
    def __init__(self, svg=None, width=640, height=480, title=None):
        """
        Initializes the Pygame window.

        Args:
            width (int): Width of the window.
            height (int): Height of the window.
            title (str) : Title of the window.
        """
        pygame.init()  # pylint: disable=no-member
        self._svg_source = None
        self._svg_tree = None
        if svg:
            self.update(svg)

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
        im = im[:, :, :3].transpose(1, 0, 2)[:, :, ::-1].copy()
        return im

    def svg_to_npim(self, svg_bytestring, dpi=100):
        """Renders a svg bytestring as a RGB image in a numpy array"""
        tree = cairosvg.parser.Tree(bytestring=svg_bytestring)
        surf = cairosvg.surface.PNGSurface(tree, None, dpi).cairo
        return self.surface_to_npim(surf)

    def update(self, svg):
        self._svg_source = svg
        self._svg_tree = ET.fromstring(svg)
        self._event_tags = find_all_mouse_event_elements(self._svg_source)

    def render(self):
        self.render_svg(self._svg_source)

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


def find_all_mouse_event_elements(root: ET._Element):
    tags = [
        "onmousedown",
        "onmouseup",
        "onmouseover",
        "onmouseout",
        "onmouseleave",
        "onmouseenter",
        "onmousemove",
        "onclick",
        "onmouseclick",
    ]

    def _gen():
        for tag in tags:
            elements = [element for element in root.xpath(f"//*[@{tag}]")]
            yield tag, elements

    result = dict(_gen())
    # update the alias to have consistent naming -_-
    result["onmouseclick"].extend(result["onclick"])
    del result["onclick"]
    return result


def point_in_rect(x, y, rect):
    """Determine if a point is inside a rectangle."""
    rx, ry, width, height = [
        float(rect.get(attr)) for attr in ("x", "y", "width", "height")
    ]
    return rx <= x <= rx + width and ry <= y <= ry + height


def point_in_circle(x, y, circle):
    """Determine if a point is inside a circle."""
    cx, cy, r = [float(circle.get(attr)) for attr in ("cx", "cy", "r")]
    return math.sqrt((x - cx) ** 2 + (y - cy) ** 2) <= r


def apply_viewbox_transform(point, viewBox, svg_size):
    """Apply viewBox transformation to a point."""
    if not viewBox:
        return point  # No transformation needed

    vb_x, vb_y, vb_width, vb_height = [float(v) for v in viewBox.split()]
    svg_width, svg_height = svg_size

    # Simple proportional scaling based on width and height
    x = (point[0] / svg_width) * vb_width + vb_x
    y = (point[1] / svg_height) * vb_height + vb_y

    return x, y


def apply_inverse_viewbox_transform(transformed_point, viewBox, svg_size):
    """Apply inverse viewBox transformation to a point."""
    if not viewBox:
        return transformed_point  # No transformation needed

    vb_x, vb_y, vb_width, vb_height = [float(v) for v in viewBox.split()]
    svg_width, svg_height = svg_size

    # Inverse proportional scaling and translation
    x = (transformed_point[0] - vb_x) * (svg_width / vb_width)
    y = (transformed_point[1] - vb_y) * (svg_height / vb_height)

    return x, y


def element_hit_test(svg_element, point, symbols={}):
    """Recursively search the parent heirarchy transforming the point and checking if it is contained in the element"""

    # TODO
    # def parent_heirarchy(svg_element):
    #     while svg_element.parent:
    #         yield svg_element

    # for parent in parent_heirarchy(svg_element):
    #     viewbox = parent.get("viewBox")
    #     if viewbox:
    #         apply_viewbox_transform(point, viewbox)

    # if svg_root.tag.endswith('svg'):
    #     # Handle viewBox transformation
    #     viewBox = svg_root.get('viewBox')
    #     if viewBox:
    #         svg_size = (float(svg_root.get('width', 100)), float(svg_root.get('height', 100)))  # Defaults if not specified
    #         point = apply_viewbox_transform(point, viewBox, svg_size)

    # for element in svg_root:
    #     # Check if this element is a `use` referencing a symbol
    #     if element.tag.endswith('use'):
    #         href = element.get('{http://www.w3.org/1999/xlink}href', '')
    #         if href.startswith('#'):
    #             symbol = symbols.get(href[1:])
    #             if symbol is not None:
    #                 if find_element_at_point(symbol, point, symbols):
    #                     return True

    #     # Directly handle basic shapes
    #     elif element.tag.endswith('rect') and point_in_rect(point[0], point[1], element):
    #         return True
    #     elif element.tag.endswith('circle') and point_in_circle(point[0], point[1], element):
    #         return True
    #     elif element.tag.endswith('svg'):  # Nested SVG
    #         if find_element_at_point(element, point, symbols):
    #             return True
    #     elif element.tag.endswith('symbol'):  # Store symbol for later reference
    #         symbols[element.get('id')] = element

    # return False
