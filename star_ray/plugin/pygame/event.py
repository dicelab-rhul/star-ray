""" TODO """

# pylint: disable=no-member

from dataclasses import astuple

import pygame

from star_ray.event import (
    MouseButtonEvent,
    MouseMotionEvent,
    KeyEvent,
    ExitEvent,
    Event,
)

# constant values
PYGAME_KEYDOWN = pygame.KEYDOWN
PYGAME_KEYUP = pygame.KEYUP
PYGAME_QUIT = pygame.QUIT
PYGAME_MOUSEDOWN = pygame.MOUSEBUTTONDOWN
PYGAME_MOUSEUP = pygame.MOUSEBUTTONUP
PYGAME_MOUSEMOTION = pygame.MOUSEMOTION


class _EventFactory:
    @staticmethod
    def create_exit_event_from_pygame_event(pygame_event: pygame.event.EventType):
        assert pygame_event.type == PYGAME_QUIT
        return ExitEvent(*astuple(Event.new("pygame")))

    @staticmethod
    def create_key_event_from_pygame_event(pygame_event):
        """Creates a [KeyEvent] instance from a [pygame] keyboard event.

        Args:
            pygame_event ([pygame.Event]): The [pygame] event from which to create the KeyEvent.

        Returns:
            KeyEvent: A new instance of KeyEvent initialized with the pygame event data.

        Raises:
            ValueError: If the provided pygame event is not a KEYDOWN or KEYUP event.
        """
        if pygame_event.type not in (PYGAME_KEYDOWN, PYGAME_KEYUP):
            raise ValueError(
                "The provided pygame event is not a KEYDOWN or KEYUP event."
            )

        status = (
            KeyEvent.PRESS if pygame_event.type == PYGAME_KEYDOWN else KeyEvent.RELEASE
        )
        # TODO implement and update KeyEvent.new
        return KeyEvent(
            *astuple(Event.new("pygame")),
            key=pygame_event.key,
            key_name=pygame.key.name(pygame_event.key),
            status=status,
        )

    @staticmethod
    def create_mouse_button_event_from_pygame_event(pygame_event):
        """
        Creates a [MouseButtonEvent] instance from a [pygame] mouse event.

        Args:
            pygame_event (pygame.Event): The [pygame] event from which to create the MouseButtonEvent.

        Returns:
            [MouseButtonEvent]: A new instance of [MouseButtonEvent] initialized with the [pygame] event data.

        Raises:
            ValueError: If the provided [pygame] event is not a [pygame.MOUSEBUTTONDOWN] or [pygame.MOUSEBUTTONUP] event.
        """
        if pygame_event.type not in (PYGAME_MOUSEDOWN, PYGAME_MOUSEUP):
            raise ValueError(
                "The provided pygame event is not a MOUSEBUTTONDOWN or MOUSEBUTTONUP event."
            )

        status = (
            MouseButtonEvent.DOWN
            if pygame_event.type == PYGAME_MOUSEDOWN
            else MouseButtonEvent.UP
        )
        return MouseButtonEvent.new(
            "pygame",
            button=pygame_event.button,
            position=pygame_event.pos,
            status=status,
        )

    @staticmethod
    def create_mouse_motion_event_from_pygame_event(pygame_event):
        """
        Creates a [MouseMotionEvent] instance from a [pygame] mouse movement event.

        Args:
            pygame_event ([pygame.Event]): The [pygame] event from which to create the MouseMotionEvent.

        Returns:
            [MouseMotionEvent]: A new instance of [MouseMotionEvent] initialized with the [pygame] event data.

        Raises:
            ValueError: If the provided [pygame] event is not a [pyame.MOUSEMOTION] event.
        """
        if pygame_event.type != PYGAME_MOUSEMOTION:
            raise ValueError("The provided pygame event is not a MOUSEMOTION event.")

        return MouseMotionEvent.new(
            "pygame", position=pygame_event.pos, relative=pygame_event.rel
        )
