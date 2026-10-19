from src.game.core.level import Level
from src.game.core.move import Move
from src.game.core.state import State
from src.game.logic.engine import BloxorzGame
from src.solver_algorithms.core.cost_calculator_type import CostCalculatorType
from src.solver_algorithms.core.heuristic_calculator_type import HeuristicCalculatorType
from src.solver_algorithms.frontiers.Stack import Stack
from src.solver_algorithms.solvers.solver import Solver


class DFSSolver(Solver):
    def __init__(
        self,
        engine: BloxorzGame,
        level: Level | None = None,
        cost_calculator_type: CostCalculatorType | None = None,
        heuristic_calculator_type: HeuristicCalculatorType | None = None,
    ) -> None:
        super().__init__(engine)

        self.frontier = Stack()

    def _can_process_move(self, current_state: State, move: Move) -> bool:
        next_state = move[1]
        return next_state not in self.visited and not self.frontier.contains(next_state)

    def _update_internal_states(
        self,
        current_state: State,
        next_move: Move,
    ) -> None:
        next_state = next_move[1]
        self._update_frontier_with_state_difference(current_state, next_state)
        self._update_parent_map_with_move(current_state, next_move)

    def _reset_internal_states(self) -> None:
        self.visited = set()
        self.frontier = Stack()
        self.parent_map = {}

    def _calculate_priority(self, current_state: State, next_state: State) -> float:
        return self._calculate_cost(
            current_state, next_state
        ) + self._calculate_heuristic(next_state)

    def _calculate_cost(self, current_state: State, next_state: State) -> float:
        return 1

    def _calculate_heuristic(self, state: State) -> float:
        return 0
