from typing import ClassVar

from src.game.core.state import State
from src.solver_algorithms.cost.cost_calculator import CostCalculator
from src.solver_algorithms.cost.move_info_determiner import MoveInfoDeterminer


class EffortCostCalculator(CostCalculator):
    """Physical effort: lifting the block from lying to standing raises its centre
    of mass, so it costs more than tipping it over or rolling it sideways.

    - STAND_UP_COST for a roll that ends with the 1x1x2 block standing up,
    - ROLL_COST for every other roll, mini cube move or cube switch.
    Every cost is >= 1, which the admissible heuristics rely on.
    """

    ROLL_COST: ClassVar[float] = 1
    STAND_UP_COST: ClassVar[float] = 2

    def calculate_cost(self, current_state: State, next_state: State) -> float:
        if MoveInfoDeterminer.is_stand_up(current_state, next_state):
            return self.STAND_UP_COST

        return self.ROLL_COST
