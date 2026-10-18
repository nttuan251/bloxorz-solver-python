"""A* Search with the admissible heuristic in heuristics.py."""

from __future__ import annotations

import heapq
import itertools

from ..core.game import BloxorzGame
from ..core.state import State
from ..core.tile import Action
from .base import Solution, solve_with_stats
from .heuristics import heuristic


def solve_astar(game: BloxorzGame, start: State | None = None) -> Solution:
    start = start if start is not None else game.start_state()
    level = game.level

    def run():
        counter = itertools.count()
        h0 = heuristic(start, level)
        frontier: list[tuple[float, int, float, State]] = \
            [(h0, next(counter), 0.0, start)]
        parent: dict[State, tuple[State | None, Action | None]] = \
            {start: (None, None)}
        g: dict[State, float] = {start: 0.0}
        expanded = 0
        if game.is_goal(start):
            return start, parent, expanded
        while frontier:
            _, _, cost_u, u = heapq.heappop(frontier)
            if cost_u > g[u]:
                continue
            expanded += 1
            for act, nxt, step in game.successors(u):
                ng = cost_u + step
                if nxt not in g or ng < g[nxt] - 1e-12:
                    g[nxt] = ng
                    parent[nxt] = (u, act)
                    if game.is_goal(nxt):
                        return nxt, parent, expanded
                    f = ng + heuristic(nxt, level)
                    heapq.heappush(frontier, (f, next(counter), ng, nxt))
        return None, parent, expanded

    return solve_with_stats(game, run)
