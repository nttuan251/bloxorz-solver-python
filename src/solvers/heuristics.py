"""Admissible heuristic for A* (uniform cost 1 per move)."""

from __future__ import annotations

from ..core.level import Level
from ..core.state import State


def heuristic(s: State, level: Level) -> float:
    gr, gc = level.goal
    if s.split:
        d = min(abs(s.a[0] - gr) + abs(s.a[1] - gc),
                abs(s.b[0] - gr) + abs(s.b[1] - gc))
        # Cubes move 1 cell/roll, block moves up to 2: /2 stays admissible.
        return d / 2.0
    if s.is_standing():
        d = abs(s.a[0] - gr) + abs(s.a[1] - gc)
        return d / 2.0
    d = min(abs(s.a[0] - gr) + abs(s.a[1] - gc),
            abs(s.b[0] - gr) + abs(s.b[1] - gc))
    # Lying needs >= 1 extra roll to stand on the goal.
    return d / 2.0 + 0.5
