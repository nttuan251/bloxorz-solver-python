"""Shared enums for core game logic (no Ursina dependency)."""

from enum import Enum


class Action(str, Enum):
    UP = "UP"
    DOWN = "DOWN"
    LEFT = "LEFT"
    RIGHT = "RIGHT"
    SWITCH = "SWITCH"  # spacebar: switch active cube when split

    def __str__(self) -> str:  # pragma: no cover
        return self.value


# Canonical order used by all solvers for determinism.
ACTION_ORDER = (Action.UP, Action.DOWN, Action.LEFT, Action.RIGHT, Action.SWITCH)


class SwitchKind(str, Enum):
    SOFT = "soft"
    HEAVY = "heavy"
    SPLIT = "split"


class BridgeMode(str, Enum):
    TOGGLE = "toggle"  # flip open/closed on every entry
    OPEN = "open"      # permanent: set to open after activation
    CLOSED = "closed"  # permanent: set to closed after activation
