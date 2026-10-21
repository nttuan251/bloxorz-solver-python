from typing import ClassVar

from src.game.core.state import State
from src.solver_algorithms.cost_calculator.cost_calculator import CostCalculator
from src.solver_algorithms.cost_calculator.move_features import MoveFeatures


class SplitAwareCostCalculator(CostCalculator):
    """Steering two separate mini cubes is harder than rolling one block.

    - CUBE_MOVE_COST for moving a mini cube while split (the merging move included),
    - SWITCH_CONTROL_COST for switching the controlled cube,
    - ROLL_COST for every roll of the whole 1x1x2 block.
    Every cost is >= 1, which the admissible heuristics rely on.
    """

    ROLL_COST: ClassVar[float] = 1
    CUBE_MOVE_COST: ClassVar[float] = 2
    SWITCH_CONTROL_COST: ClassVar[float] = 1

    def calculate_cost(self, current_state: State, next_state: State) -> float:
        if MoveFeatures.is_switch_control(current_state, next_state):
            return self.SWITCH_CONTROL_COST

        if MoveFeatures.is_cube_move(current_state, next_state):
            return self.CUBE_MOVE_COST

        return self.ROLL_COST
