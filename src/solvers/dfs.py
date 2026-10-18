"""Depth-First Search (graph search with visited set to avoid cycles)."""

from __future__ import annotations

from ..core.game import BloxorzGame
from ..core.state import State
from ..core.tile import Action
from .base import Solution, solve_with_stats


def solve_dfs(game: BloxorzGame, start: State | None = None) -> Solution:
    start = start if start is not None else game.start_state()

    def run():
        if game.is_goal(start):
            return start, {start: (None, None)}, 0
        stack: list[State] = [start]
        parent: dict[State, tuple[State | None, Action | None]] = \
            {start: (None, None)}
        expanded = 0
        while stack:
            cur = stack.pop()
            expanded += 1
            # Reversed so UP is expanded first (same order as BFS successors).
            for act, nxt, _ in reversed(game.successors(cur)):
                if nxt in parent:
                    continue
                parent[nxt] = (cur, act)
                if game.is_goal(nxt):
                    return nxt, parent, expanded
                stack.append(nxt)
        return None, parent, expanded

    return solve_with_stats(game, run)
