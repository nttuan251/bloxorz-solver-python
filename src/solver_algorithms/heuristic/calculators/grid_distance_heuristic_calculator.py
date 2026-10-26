import math

from src.game.core.coordinate import Coordinate
from src.game.core.level import Level
from src.solver_algorithms.heuristic.calculators.teleport_aware_heuristic_calculator import (
    TeleportAwareHeuristicCalculator,
)


class GridDistanceHeuristicCalculator(TeleportAwareHeuristicCalculator):
    def __init__(self, level: Level) -> None:
        targets = [level.get_goal()] + [
            switch for switch, _ in level.get_split_switches()
        ]
        self.tile_distances = {
            target: level.get_tile_distances_from_source(target) for target in targets
        }

        super().__init__(level)

    def _actions_to_reach(self, coords1: Coordinate, coords2: Coordinate) -> float:
        distance = self.tile_distances[coords2].get(coords1)

        if distance is None:
            return math.inf

        return math.ceil(distance / 2)
