from abc import ABC, abstractmethod

from game.core.action import Action
from game.core.level import Level
from game.core.move import Move
from game.core.state import State
from game.logic.engine import BloxorzGame
from solvers.frontiers.Frontier import Frontier


class Solver(ABC):
    frontier: Frontier

    def __init__(self, engine: BloxorzGame, level: Level | None = None) -> None:
        self.engine = engine
        self.level = level

        self.visited: set[State] = set()
        self.parent_map: dict[State, tuple[Action, State, float]] = {}

    def solve(self) -> tuple[list[Action], float]:
        self.frontier.push(self.engine.start_state(), 0)

        while True:
            current_state = self.frontier.pop()

            if current_state is None:
                return ([], 0)

            if current_state in self.visited:
                continue

            if self.engine.is_goal(current_state):
                path, total_cost = self.construct_path_and_aggregate_cost(current_state)
                return (path, total_cost)

            self.mark_visited(current_state)
            self.process_moves(current_state)

    def mark_visited(self, state: State) -> None:
        self.visited.add(state)

    def construct_path_and_aggregate_cost(
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

    def process_moves(self, current_state: State) -> None:
        next_moves = self.engine.successors(current_state)

        for next_move in next_moves:
            if self.can_process_move(current_state, next_move):
                self.update_internal_states(current_state, next_move)

    def update_frontier_with_state_difference(
        self, current_state: State, next_state: State
    ) -> None:
        self.frontier.push(
            next_state, self.calculate_priority(current_state, next_state)
        )

    def update_parent_map_with_move(
        self, current_state: State, next_move: Move
    ) -> None:
        action, next_state = next_move
        cost = self.calculate_cost(current_state, next_state)

        self.parent_map[next_state] = (action, current_state, cost)

    @abstractmethod
    def update_internal_states(
        self,
        current_state: State,
        next_move: Move,
    ) -> None:
        pass

    @abstractmethod
    def can_process_move(self, current_state: State, move: Move) -> bool:
        pass

    @abstractmethod
    def calculate_priority(self, current_state: State, next_state: State) -> float:
        pass

    @abstractmethod
    def calculate_cost(self, current_state: State, next_state: State) -> float:
        pass

    @abstractmethod
    def calculate_heuristic(self, state: State) -> float:
        pass
