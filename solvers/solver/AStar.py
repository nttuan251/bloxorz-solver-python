from collections.abc import Callable

from core.Action import Action
from core.state import move_type, state_type

from solvers.frontier.PQueue import PQueue
from solvers.solver.Solver import Solver


class AStar(Solver):
    def __init__(
        self,
        initial_state: state_type,
        get_next_moves: Callable[[state_type], list[move_type]],
        is_goal: Callable[[state_type], bool],
    ) -> None:
        super().__init__(initial_state, get_next_moves, is_goal)

        self.frontier = PQueue()
        self.min_costs: dict[state_type, float] = {initial_state: 0}

    def update_frontier_and_parent_map_with_next_move(
        self,
        current_state: state_type,
        next_move: move_type,
    ) -> None:
        next_state: state_type = next_move[0]
        action_from_current_state: Action = next_move[1]
        move_cost = next_move[2]

        total_cost_to_next_state = self.min_costs[current_state] + move_cost

        if total_cost_to_next_state < self.min_costs.get(next_state, float("inf")):
            self.min_costs[next_state] = total_cost_to_next_state

            self.frontier.push(next_state, total_cost_to_next_state)
            self.parent_map[next_state] = (
                current_state,
                action_from_current_state,
                move_cost,
            )
