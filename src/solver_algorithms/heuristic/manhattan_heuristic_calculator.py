from src.game.core.coordinate import Coordinate
from src.game.core.level import Level
from src.game.core.state import State
from src.solver_algorithms.heuristic.heuristic_calculator import HeuristicCalculator


class ManhattanHeuristicCalculator(HeuristicCalculator):
    """The heuristic suggested in the assignment, kept as a baseline for experiments.

    h = (Manhattan distance from the block's nearest cell to the goal) / 2,
        + 0.5 when the block is lying (it needs at least one more roll to stand up).

    WARNING: not guaranteed admissible, and not consistent, on levels with split
    switches. A split switch teleports the block far away in one roll, so the true
    remaining cost can be smaller than the straight-line distance: on the old
    level12_split map h = 6.5 while the true cost was 4. On the 33 JSON levels it
    never overestimates, but it breaks consistency on 26 moves (levels 08, 10, 16,
    20, 26), so A* (which never reopens expanded states) is not guaranteed to find
    an optimal path. Kept as a baseline; use TELEPORT_AWARE or stronger instead.
    """

    LYING_PENALTY = 0.5

    def __init__(self, level: Level) -> None:
        super().__init__(level)

        self.goal = level.get_goal()

    def calculate_heuristic(self, state: State) -> float:
        cells = {state.get_first_coords(), state.get_second_coords()}
        distance = min(self._manhattan_distance(coords, self.goal) for coords in cells)

        if state.is_split() or state.is_standing():
            return distance / 2

        return distance / 2 + self.LYING_PENALTY

    def _manhattan_distance(self, coords1: Coordinate, coords2: Coordinate) -> int:
        return abs(coords1[0] - coords2[0]) + abs(coords1[1] - coords2[1])
