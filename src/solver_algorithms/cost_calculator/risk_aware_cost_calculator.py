from typing import ClassVar

from game.core.coordinate import Coordinate
from game.core.state import State
from solver_algorithms.cost_calculator.cost_calculator import CostCalculator


class RiskAwareCostCalculator(CostCalculator):
    """Non-uniform cost: risky moves onto fragile tiles cost more.

    - ROLL_COST for a normal roll or a mini cube move,
    - FRAGILE_COST if any cell the moving block / cube lands on is fragile,
    - SWITCH_CONTROL_COST for switching the controlled cube while split
      (the team counts it as a move, see docs/DECISIONS.md).
    Every cost is >= 1, which TeleportAwareHeuristicCalculator relies on.
    """

    ROLL_COST: ClassVar[float] = 1
    FRAGILE_COST: ClassVar[float] = 2
    SWITCH_CONTROL_COST: ClassVar[float] = 1

    def calculate_cost(self, current_state: State, next_state: State) -> float:
        if self._is_switch_control(current_state, next_state):
            return self.SWITCH_CONTROL_COST

        landed_cells = self._get_landed_cells(current_state, next_state)

        if any(self.level.is_fragile_tile(coords) for coords in landed_cells):
            return self.FRAGILE_COST

        return self.ROLL_COST

    @staticmethod
    def _is_switch_control(current_state: State, next_state: State) -> bool:
        return (
            current_state.is_split()
            and next_state.is_split()
            and current_state.get_first_coords() == next_state.get_first_coords()
            and current_state.get_second_coords() == next_state.get_second_coords()
            and current_state.get_controlled_cube_coords()
            != next_state.get_controlled_cube_coords()
        )

    @staticmethod
    def _get_landed_cells(current_state: State, next_state: State) -> set[Coordinate]:
        new_cells = {next_state.get_first_coords(), next_state.get_second_coords()}

        if not current_state.is_split():
            return new_cells

        # When split, only the moved cube lands; the other one stays put.
        old_cells = {current_state.get_first_coords(), current_state.get_second_coords()}
        return (new_cells - old_cells) or new_cells
