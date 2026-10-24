from src.game.core.state import State
from src.solver_algorithms.heuristic.heuristic_calculator import HeuristicCalculator


class TrivialHeuristicCalculator(HeuristicCalculator):
    def calculate_heuristic(self, state: State) -> float:
        return 0
