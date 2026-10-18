"""Breadth-First Search (optimal with uniform cost 1)."""

from __future__ import annotations

from collections import deque

from ..core.game import BloxorzGame
from ..core.state import State
from ..core.tile import Action
from .base import Solution, solve_with_stats


def solve_bfs(game: BloxorzGame, start: State | None = None) -> Solution:
    start = start if start is not None else game.start_state()

    def run():
        if game.is_goal(start):
            return start, {start: (None, None)}, 0
        frontier: deque[State] = deque([start])
        parent: dict[State, tuple[State | None, Action | None]] = \
            {start: (None, None)}
        expanded = 0
        while frontier:
            cur = frontier.popleft()
            expanded += 1
            for act, nxt, _ in game.successors(cur):
                if nxt in parent:
                    continue
                parent[nxt] = (cur, act)
                if game.is_goal(nxt):
                    return nxt, parent, expanded
                frontier.append(nxt)
        return None, parent, expanded

    return solve_with_stats(game, run)
