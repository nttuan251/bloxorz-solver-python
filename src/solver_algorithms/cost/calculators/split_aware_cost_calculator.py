from typing import ClassVar

from src.game.core.state import State
from src.solver_algorithms.cost.cost_calculator import CostCalculator
from src.solver_algorithms.cost.move_info_determiner import MoveInfoDeterminer


class SplitAwareCostCalculator(CostCalculator):
    ROLL_COST: ClassVar[float] = 1
    CUBE_MOVE_COST: ClassVar[float] = 2
    SWITCH_CONTROL_COST: ClassVar[float] = 0

    def calculate_cost(self, current_state: State, next_state: State) -> float:
        if MoveInfoDeterminer.is_switch_control(current_state, next_state):
            return self.SWITCH_CONTROL_COST

        if MoveInfoDeterminer.is_mini_cube_move(current_state, next_state):
            return self.CUBE_MOVE_COST

        return self.ROLL_COST
