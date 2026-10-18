"""Pure game flow controller (no Ursina) - testable, used by GUI + video."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from core.game import BloxorzGame
from core.level import Level
from core.loader import load_level
from core.state import State
from core.tile import Action


class GameController:
    """Holds Level + current State, exposes manual play + replay for GUI."""

    def __init__(self, level: Level):
        self.level = level
        self.game = BloxorzGame(level)
        self.start = self.game.start_state()
        self.state: State = self.start
        self.history: list[State] = [self.start]
        self.status = "playing"  # playing | won | lost
        self.fell_action: Action | None = None

    @classmethod
    def from_file(cls, path: str | Path) -> "GameController":
        return cls(load_level(path))

    def restart(self) -> State:
        self.state = self.start
        self.history = [self.start]
        self.status = "playing"
        self.fell_action = None
        return self.state

    def reset_to(self, state: State) -> State:
        self.state = state
        self.history = [state]
        self.status = "playing"
        self.fell_action = None
        return self.state

    def do_action(self, action: Action) -> tuple[State | None, str]:
        """Apply one action. Returns (state|None, event)."""
        if self.status != "playing":
            return self.state, "ignored"
        if action == Action.SWITCH and not self.state.split:
            return self.state, "ignored"
        nxt = self.game.apply(self.state, action)
        if nxt is None:
            self.status = "lost"
            self.fell_action = action
            return None, "fell"
        was_split = self.state.split
        self.state = nxt
        self.history.append(nxt)
        if self.game.is_goal(nxt):
            self.status = "won"
            return nxt, "won"
        if not was_split and nxt.split:
            return nxt, "split"
        if was_split and not nxt.split:
            return nxt, "merged"
        if action == Action.SWITCH:
            return nxt, "switched"
        return nxt, "moved"
