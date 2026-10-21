import math

from src.game.core.coordinate import Coordinate
from src.game.core.level import Level
from src.solver_algorithms.heuristic.teleport_aware_heuristic_calculator import (
    TeleportAwareHeuristicCalculator,
)


class GridDistanceHeuristicCalculator(TeleportAwareHeuristicCalculator):
    """TELEPORT_AWARE with walking distance on the tiles instead of straight-line distance.

    The distance between two cells is the fewest 4-neighbour steps walking only on
    tiles (every bridge treated as open), so holes in the board are taken into
    account. It is at least the Manhattan distance, so the heuristic is at least as
    strong as TELEPORT_AWARE.

    Admissible and consistent for any cost function with every cost >= 1: a roll
    moves each cell of the block onto a neighbouring tile, so the walking distance
    of the block's nearest cell drops by at most 2 per roll (1 per mini cube move),
    and the same argument as TELEPORT_AWARE applies. Cells that cannot reach the
    goal even with every bridge open get an infinite bound (they are dead ends).
    """

    def __init__(self, level: Level) -> None:
        targets = [level.get_goal()] + [switch for switch, _ in level.get_split_switches()]
        self.tile_distances = {
            target: level.get_tile_distances_from(target) for target in targets
        }

        super().__init__(level)

    def _actions_to_reach(self, coords1: Coordinate, coords2: Coordinate) -> float:
        distance = self.tile_distances[coords2].get(coords1)

        if distance is None:
            return math.inf

        return math.ceil(distance / 2)
