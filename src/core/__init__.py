"""Public interface of the core package (GUI + solvers talk through this)."""

from .game import BloxorzGame
from .level import BridgeGroup, Level, Switch
from .loader import load_level
from .state import State
from .tile import ACTION_ORDER, Action, BridgeMode, SwitchKind

__all__ = [
    "BloxorzGame", "Level", "Switch", "BridgeGroup", "State",
    "Action", "ACTION_ORDER", "SwitchKind", "BridgeMode", "load_level",
]
