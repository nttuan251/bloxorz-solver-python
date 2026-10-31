from src.game.core.level import Level
from src.game.core.move import Move
from src.game.core.state import State
from src.game.logic.engine import BloxorzGame
from src.solver_algorithms.core.cost_calculator_type import CostCalculatorType
from src.solver_algorithms.core.heuristic_calculator_type import HeuristicCalculatorType
from src.solver_algorithms.cost.cost_calculator_factory import (
    CostCalculatorFactory,
)
from src.solver_algorithms.frontiers.PQueue import PQueue
from src.solver_algorithms.heuristic.heuristic_calculator_factory import (
    HeuristicCalculatorFactory,
)
from src.solver_algorithms.solvers.solver import Solver


class AStarSolver(Solver):
    def __init__(
        self,
        engine: BloxorzGame,
        level: Level,
        cost_calculator_type: CostCalculatorType,
        heuristic_calculator_type: HeuristicCalculatorType,
    ) -> None:
        super().__init__(engine)

        self.level = level
        self.cost_calculator = CostCalculatorFactory.create(cost_calculator_type, level)
        self.heuristic_calculator = HeuristicCalculatorFactory.create(
            heuristic_calculator_type, level
        )

        self.frontier = PQueue()
        self.min_costs: dict[State, float] = {self.engine.start_state(): 0}

    def _can_process_move(self, current_state: State, move: Move) -> bool:
        next_state = move[1]
        move_cost = self._calculate_cost(current_state, next_state)
        total_cost_to_next_state = self.min_costs[current_state] + move_cost

        return total_cost_to_next_state < self.min_costs.get(next_state, float("inf"))

    def _update_internal_states(
        self,
        current_state: State,
        next_move: Move,
    ) -> None:
        next_state = next_move[1]
        move_cost = self._calculate_cost(current_state, next_state)
        total_cost_to_next_state = self.min_costs[current_state] + move_cost

        self._update_frontier_with_state_difference(current_state, next_state)
        self._update_parent_map_with_move(current_state, next_move)
        self.min_costs[next_state] = total_cost_to_next_state

    def _reset_internal_states(self) -> None:
        self.visited = set()
        self.frontier = PQueue()
        self.parent_map = {}
        self.min_costs = {self.engine.start_state(): 0}

    def _calculate_priority(self, current_state: State, next_state: State) -> float:
        return (
            self._calculate_cost(current_state, next_state)
            + self.min_costs[current_state]
            + self._calculate_heuristic(next_state)
        )

    def _calculate_cost(self, current_state: State, next_state: State) -> float:
        return self.cost_calculator.calculate_cost(current_state, next_state)

    def _calculate_heuristic(self, state: State) -> float:
        return self.heuristic_calculator.calculate_heuristic(state)
