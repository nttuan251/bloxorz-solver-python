from game.core.state import State
from solver_algorithms.cost_calculator.cost_calculator import CostCalculator


class UniformCostCalculator(CostCalculator):
    def calculate_cost(self, current_state: State, next_state: State) -> float:
        return 1
