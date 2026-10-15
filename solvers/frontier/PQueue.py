import heapq

from core.state import state_type

from solvers.frontier.Frontier import Frontier

internal_state_type = tuple[float, state_type]


class PQueue(Frontier):
    def __init__(self) -> None:
        super().__init__()
        self.data: list[internal_state_type] = []

    def contains(self, state: state_type) -> bool:
        return state in [
            self.convert_to_external_format(internal_state)
            for internal_state in self.data
        ]
        # Extremely inefficient here, but this function should never be used in the main solver.

    def push(self, state: state_type, current_min_cost: float | None) -> None:
        if current_min_cost is None:
            raise (Exception("Total cost is missing. Cannot calculate priority"))

        internal_state = self.convert_to_internal_format(state, current_min_cost)
        heapq.heappush(self.data, internal_state)

    def pop(self) -> state_type | None:
        if len(self.data) == 0:
            return None
        internal_state = heapq.heappop(self.data)
        state = self.convert_to_external_format(internal_state)

        return state

    def convert_to_internal_format(
        self, state: state_type, current_min_cost: float
    ) -> internal_state_type:
        return (state[2] + current_min_cost, state)

    def convert_to_external_format(
        self, internal_state: internal_state_type
    ) -> state_type:
        return internal_state[1]
