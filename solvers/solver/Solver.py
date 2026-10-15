from abc import ABC, abstractmethod
from collections.abc import Callable

from core.Action import Action
from core.state import move_type, state_type

from solvers.frontier.Frontier import Frontier


class Solver(ABC):
    frontier: Frontier

    def __init__(
        self,
        initial_state: state_type,
        get_next_moves: Callable[[state_type], list[move_type]],
        is_goal: Callable[[state_type], bool],
    ) -> None:
        self.initial_state = initial_state
        self.get_next_moves = get_next_moves
        self.is_goal = is_goal

        self.visited: set[state_type] = set()
        self.parent_map: dict[state_type, move_type] = {}

    def solve(self) -> tuple[list[Action], float]:
        self.frontier.push(self.initial_state)

        while True:
            current_state = self.frontier.pop()

            if current_state is None:
                return ([], 0)

            if current_state in self.visited:
                continue

            if self.is_goal(current_state):
                path, total_cost = self.construct_path_and_calculate_cost(current_state)
                return (path, total_cost)

            self.mark_visited(current_state)
            self.process_next_states(current_state)

    def mark_visited(self, state: state_type) -> None:
        self.visited.add(state)

    def construct_path_and_calculate_cost(
        self, goal_state: state_type
    ) -> tuple[list[Action], float]:
        path: list[Action] = []
        total_cost = 0

        current_state = goal_state
        while current_state != self.initial_state:
            previous_state, action, cost = self.parent_map[current_state]

            path.insert(0, action)
            total_cost += cost

            current_state = previous_state

        return path, total_cost

    def process_next_states(self, current_state: state_type) -> None:
        next_state_and_actions = self.get_next_moves(current_state)

        for next_state_and_action in next_state_and_actions:
            self.update_frontier_and_parent_map_with_next_move(
                current_state, next_state_and_action
            )

    @abstractmethod
    def update_frontier_and_parent_map_with_next_move(
        self,
        current_state: state_type,
        next_move: move_type,
    ) -> None:
        pass
