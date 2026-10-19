import math

from game.core.coordinate import Coordinate
from game.core.level import Level
from game.core.state import State
from solver_algorithms.heuristic.heuristic_calculator import HeuristicCalculator


class TeleportAwareHeuristicCalculator(HeuristicCalculator):
    """Admissible and consistent heuristic for any cost function with every cost >= 1.

    It is a lower bound on the number of actions still needed, hence on the cost.
    One roll moves the block's nearest cell at most 2 cells closer to a target and
    a mini cube move at most 1, so reaching a target at distance d needs at least
    ceil(d / 2) actions. A split switch teleports the block, so the bound of a cell
    is the cheaper of going straight to the goal or through a split switch:

        bound(x) = min(ceil(|x - goal| / 2),
                       min over split switches p of ceil(|x - p| / 2) + after_teleport(p))
        after_teleport(p) = min over the two destinations c of bound(c)

    Extra terms: a split block needs at least 2 more actions (one cube move to
    merge, one roll to stand up), and a block lying across the goal also needs at
    least 2 (no single roll stands it on a cell it covers).
    """

    def __init__(self, level: Level) -> None:
        super().__init__(level)

        self.goal = level.get_goal()
        self.split_switches = level.get_split_switches()
        self.after_teleport = self._calculate_after_teleport_bounds()

    def calculate_heuristic(self, state: State) -> float:
        cells = {state.get_first_coords(), state.get_second_coords()}
        bound = min(self._bound(coords, self.after_teleport) for coords in cells)

        if state.is_split():
            return max(bound, 2)

        if not state.is_standing() and bound == 0:
            return 2

        return bound

    def _calculate_after_teleport_bounds(self) -> dict[Coordinate, int]:
        # Fixed point over the split switches; values only decrease, so it ends.
        min_actions_after_teleport = {
            switch: min(
                self._actions_to_reach(landing, self.goal) for landing in landing_cells
            )
            for switch, landing_cells in self.split_switches
        }

        found_improvement = True
        while found_improvement:
            found_improvement = False

            for switch, landing_cells in self.split_switches:
                best_from_landing = min(
                    self._bound(landing, min_actions_after_teleport)
                    for landing in landing_cells
                )

                if best_from_landing < min_actions_after_teleport[switch]:
                    min_actions_after_teleport[switch] = best_from_landing
                    found_improvement = True

        return min_actions_after_teleport

    def _bound(self, coords: Coordinate, after_teleport: dict[Coordinate, int]) -> int:
        route_straight_to_goal = self._actions_to_reach(coords, self.goal)
        best = route_straight_to_goal

        for switch, _ in self.split_switches:
            route_to_goal_through_switch = (
                self._actions_to_reach(coords, switch) + after_teleport[switch]
            )

            best = min(best, route_to_goal_through_switch)

        return best

    def _actions_to_reach(self, coords1: Coordinate, coords2: Coordinate) -> int:
        return math.ceil(self._manhattan_distance(coords1, coords2) / 2)

    def _manhattan_distance(self, coords1: Coordinate, coords2: Coordinate) -> int:
        return abs(coords1[0] - coords2[0]) + abs(coords1[1] - coords2[1])
