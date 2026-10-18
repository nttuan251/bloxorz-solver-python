from dataclasses import dataclass

from game.core.action import Action


@dataclass(frozen=True)
class SolutionWithMetrics:
    solution: tuple[list[Action], float]
    search_time_in_secs: float
    peak_memory_in_mb: float
    expanded_notes: int
    solution_length: int
