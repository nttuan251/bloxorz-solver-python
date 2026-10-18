from game.core.level import Level
from game.core.move import Move
from game.core.state import State
from game.logic.engine import BloxorzGame
from solvers.core.Solver import Solver
from solvers.frontiers.PQueue import PQueue


class AStar(Solver):
    def __init__(self, engine: BloxorzGame, level: Level) -> None:
        super().__init__(engine, level)

        self.frontier = PQueue()
        self.min_costs: dict[State, float] = {self.engine.start_state(): 0}

    def can_process_move(self, current_state: State, move: Move) -> bool:
        next_state = move[1]
        move_cost = self.calculate_cost(current_state, next_state)
        total_cost_to_next_state = self.min_costs[current_state] + move_cost

        return total_cost_to_next_state < self.min_costs.get(next_state, float("inf"))

    def update_internal_states(
        self,
        current_state: State,
        next_move: Move,
    ) -> None:
        next_state = next_move[1]
        move_cost = self.calculate_cost(current_state, next_state)
        total_cost_to_next_state = self.min_costs[current_state] + move_cost

        self.update_frontier_with_state_difference(current_state, next_state)
        self.update_parent_map_with_move(current_state, next_move)
        self.min_costs[next_state] = total_cost_to_next_state

    def calculate_priority(self, current_state: State, next_state: State) -> float:
        return (
            self.calculate_cost(current_state, next_state)
            + self.min_costs[current_state]
            + self.calculate_heuristic(next_state)
        )

    def calculate_cost(self, current_state: State, next_state: State) -> float:
        # TEMPORARY
        return 1

    def calculate_heuristic(self, state: State) -> float:
        # TEMPORARY
        return 0
