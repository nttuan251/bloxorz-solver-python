from src.game.core.state import State
from src.solver_algorithms.cost.cost_calculator import CostCalculator
from src.solver_algorithms.cost.move_info_determiner import MoveInfoDeterminer


class UniformCostCalculator(CostCalculator):
    def calculate_cost(self, current_state: State, next_state: State) -> float:
        # Switching control between the mini cubes is not a step (project FAQ #23).
        if MoveInfoDeterminer.is_switch_control(current_state, next_state):
            return 0

        return 1
