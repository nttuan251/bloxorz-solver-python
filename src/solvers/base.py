"""Common solver result type + measurement helpers (stdlib only)."""

from __future__ import annotations

import time
import tracemalloc
from dataclasses import dataclass, field

from ..core.game import BloxorzGame
from ..core.state import State
from ..core.tile import Action


@dataclass
class Solution:
    solved: bool
    actions: list[Action] = field(default_factory=list)
    final_state: State | None = None
    expanded: int = 0
    time_sec: float = 0.0
    peak_mem_bytes: int = 0
    solution_len: int = 0
    cost: float = 0.0

    def __post_init__(self) -> None:
        self.solution_len = len(self.actions)


class Timer:
    def __init__(self) -> None:
        self.t0 = 0.0

    def __enter__(self):
        tracemalloc.start()
        self.t0 = time.perf_counter()
        return self

    def __exit__(self, *exc):
        self.dt = time.perf_counter() - self.t0
        _, self.peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        return False


def reconstruct(parent: dict[State, tuple[State | None, Action | None]],
                end: State) -> list[Action]:
    actions: list[Action] = []
    cur: State | None = end
    while cur is not None and parent[cur][0] is not None:
        prev, act = parent[cur]
        assert act is not None
        actions.append(act)
        cur = prev
    actions.reverse()
    return actions


def solve_with_stats(game: BloxorzGame, run) -> Solution:
    """Run a search closure returning (end_state|None, parent, expanded)."""
    with Timer() as t:
        end, parent, expanded = run()
    if end is None:
        return Solution(solved=False, expanded=expanded, time_sec=t.dt,
                        peak_mem_bytes=t.peak)
    actions = reconstruct(parent, end)
    return Solution(solved=True, actions=actions, final_state=end,
                    expanded=expanded, time_sec=t.dt,
                    peak_mem_bytes=t.peak, cost=float(len(actions)))
