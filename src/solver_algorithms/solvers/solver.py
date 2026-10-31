from abc import ABC, abstractmethod

from src.game.core.action import Action
from src.game.core.level import Level
from src.game.core.move import Move
from src.game.core.state import State
from src.game.logic.engine import BloxorzGame
from src.solver_algorithms.core.cost_calculator_type import CostCalculatorType
from src.solver_algorithms.core.heuristic_calculator_type import HeuristicCalculatorType
from src.solver_algorithms.frontiers.Frontier import Frontier


class Solver(ABC):
    frontier: Frontier

    def __init__(
        self,
        engine: BloxorzGame,
        level: Level | None = None,
        cost_calculator_type: CostCalculatorType | None = None,
        heuristic_calculator_type: HeuristicCalculatorType | None = None,
    ) -> None:
        self.engine = engine

        self.visited: set[State] = set()
        self.parent_map: dict[State, tuple[Action, State, float]] = {}

    def solve(self) -> tuple[list[Action], float]:
        self._reset_internal_states()

        self.frontier.push(self.engine.start_state(), 0)

        while True:
            current_state = self.frontier.pop()

            if current_state is None:
                return ([], 0)

            if current_state in self.visited:
                continue

            if self.engine.is_goal(current_state):
                path, total_cost = self._construct_path_and_aggregate_cost(
                    current_state
                )
                return (path, total_cost)

            self._mark_visited(current_state)
            self._process_moves(current_state)

    def get_expanded_nodes(self) -> int:
        return len(self.visited) + 1

    def _mark_visited(self, state: State) -> None:
        self.visited.add(state)

    def _construct_path_and_aggregate_cost(
        self, goal_state: State
    ) -> tuple[list[Action], float]:
        path: list[Action] = []
        total_cost = 0

        start_state = self.engine.start_state()
        current_state = goal_state

        while current_state != start_state:
            action, previous_state, cost = self.parent_map[current_state]
            path.insert(0, action)
            total_cost += cost

            current_state = previous_state

        return path, total_cost

    def _process_moves(self, current_state: State) -> None:
        next_moves = self.engine.successors(current_state)

        for next_move in next_moves:
            if self._can_process_move(current_state, next_move):
                self._update_internal_states(current_state, next_move)

    def _update_frontier_with_state_difference(
        self, current_state: State, next_state: State
    ) -> None:
        self.frontier.push(
            next_state, self._calculate_priority(current_state, next_state)
        )

    def _update_parent_map_with_move(
        self, current_state: State, next_move: Move
    ) -> None:
        action, next_state = next_move
        cost = self._calculate_cost(current_state, next_state)

        self.parent_map[next_state] = (action, current_state, cost)

    @abstractmethod
    def _update_internal_states(
        self,
        current_state: State,
        next_move: Move,
    ) -> None:
        pass

    @abstractmethod
    def _reset_internal_states(self) -> None:
        pass

    @abstractmethod
    def _can_process_move(self, current_state: State, move: Move) -> bool:
        pass

    @abstractmethod
    def _calculate_priority(self, current_state: State, next_state: State) -> float:
        pass

    @abstractmethod
    def _calculate_cost(self, current_state: State, next_state: State) -> float:
        pass

    @abstractmethod
    def _calculate_heuristic(self, state: State) -> float:
        pass
