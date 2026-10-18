from game.core.move import Move
from game.core.state import State
from game.logic.engine import BloxorzGame
from solvers.core.Solver import Solver
from solvers.frontiers.Stack import Stack


class DFS(Solver):
    def __init__(self, engine: BloxorzGame) -> None:
        super().__init__(engine)

        self.frontier = Stack()

    def can_process_move(self, current_state: State, move: Move) -> bool:
        next_state = move[1]
        return next_state not in self.visited and not self.frontier.contains(next_state)

    def update_internal_states(
        self,
        current_state: State,
        next_move: Move,
    ) -> None:
        next_state = next_move[1]
        self.update_frontier_with_state_difference(current_state, next_state)
        self.update_parent_map_with_move(current_state, next_move)

    def calculate_priority(self, current_state: State, next_state: State) -> float:
        return self.calculate_cost(
            current_state, next_state
        ) + self.calculate_heuristic(next_state)

    def calculate_cost(self, current_state: State, next_state: State) -> float:
        return 1

    def calculate_heuristic(self, state: State) -> float:
        return 0
