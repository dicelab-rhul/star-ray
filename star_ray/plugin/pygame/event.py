import pygame

from dataclasses import astuple
from icua2.event import (
    MouseButtonEvent,
    MouseMotionEvent,
    KeyEvent,
    ExitEvent,
    Event,
    KEY_RELEASED,
    KEY_PRESSED,
)

PYGAME_KEYDOWN = pygame.KEYDOWN  # pylint: disable=no-member
PYGAME_KEYUP = pygame.KEYUP  # pylint: disable=no-member
PYGAME_QUIT = pygame.QUIT  # pylint: disable=no-member
PYGAME_MOUSEDOWN = pygame.MOUSEBUTTONDOWN  # pylint: disable=no-member
PYGAME_MOUSEUP = pygame.MOUSEBUTTONUP  # pylint: disable=no-member
PYGAME_MOUSEMOTION = pygame.MOUSEMOTION  # pylint: disable=no-member


class _EventFactory:
    @staticmethod
    def create_exit_event_from_pygame_event(pg_event):
        assert pg_event.type == PYGAME_QUIT
        return ExitEvent(*astuple(Event.new()))

    @staticmethod
    def create_key_event_from_pygame_event(pg_event):
        """Creates a KeyEvent instance from a Pygame keyboard event.

        Args:
            pg_event (pygame.Event): The Pygame event from which to create the KeyEvent.

        Returns:
            KeyEvent: A new instance of KeyEvent initialized with the Pygame event data.

        Raises:
            ValueError: If the provided Pygame event is not a KEYDOWN or KEYUP event.
        """
        if pg_event.type not in (PYGAME_KEYDOWN, PYGAME_KEYUP):
            raise ValueError(
                "The provided Pygame event is not a KEYDOWN or KEYUP event."
            )

        status = KEY_PRESSED if pg_event.type == PYGAME_KEYDOWN else KEY_RELEASED
        return KeyEvent(
            *astuple(Event.new()),
            key=pg_event.key,
            key_name=pygame.key.name(pg_event.key),
            status=status,
        )

    @staticmethod
    def create_mouse_button_event_from_pygame_event(pg_event):
        """
        Creates a MouseButtonEvent instance from a Pygame mouse event.

        Args:
            pg_event (pygame.Event): The Pygame event from which to create the MouseEvent.
            clickable_elements (List[xml.Element]): A list of clickable elements in the SVG.

        Returns:
            MouseEvent: A new instance of MouseEvent initialized with the Pygame event data.

        Raises:
            ValueError: If the provided Pygame event is not a MOUSEBUTTONDOWN or MOUSEBUTTONUP event.
        """
        if pg_event.type not in (PYGAME_MOUSEDOWN, PYGAME_MOUSEUP):
            raise ValueError(
                "The provided Pygame event is not a MOUSEBUTTONDOWN or MOUSEBUTTONUP event."
            )

        status = "pressed" if pg_event.type == PYGAME_MOUSEDOWN else "released"
        return MouseButtonEvent(
            *astuple(Event.new()),
            button=pg_event.button,
            position=pg_event.pos,
            status=status,
        )

    @staticmethod
    def create_mouse_motion_event_from_pygame_event(pg_event):
        """
        Creates a MouseMoveEvent instance from a Pygame mouse movement event.

        Args:
            pg_event (pygame.Event): The Pygame event from which to create the MouseMoveEvent.

        Returns:
            MouseMoveEvent: A new instance of MouseMoveEvent initialized with the Pygame event data.

        Raises:
            ValueError: If the provided Pygame event is not a MOUSEMOTION event.
        """
        if pg_event.type != PYGAME_MOUSEMOTION:
            raise ValueError("The provided Pygame event is not a MOUSEMOTION event.")

        return MouseMotionEvent(
            *astuple(Event.new()), position=pg_event.pos, relative=pg_event.rel
        )
