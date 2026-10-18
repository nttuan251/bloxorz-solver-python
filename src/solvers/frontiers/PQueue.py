import heapq

from game.core.state import State
from solvers.frontiers.Frontier import Frontier

InternalState = tuple[float, int, State]


class PQueue(Frontier):
    def __init__(self) -> None:
        super().__init__()
        self.data: list[InternalState] = []
        self.tie_breaker_counter = 0

    def contains(self, state: State) -> bool:
        return state in [
            self.convert_to_external_format(internal_state)
            for internal_state in self.data
        ]
        # Extremely inefficient here, but this function should never be used in the main solver.

    def push(self, state: State, priority: float) -> None:
        internal_state = self.convert_to_internal_format(state, priority)
        heapq.heappush(self.data, internal_state)

    def pop(self) -> State | None:
        if len(self.data) == 0:
            return None
        internal_state = heapq.heappop(self.data)
        state = self.convert_to_external_format(internal_state)

        return state

    def convert_to_internal_format(
        self, state: State, priority: float
    ) -> InternalState:
        internal_state = (priority, self.tie_breaker_counter, state)
        self.tie_breaker_counter += 1
        return internal_state

    def convert_to_external_format(self, internal_state: InternalState) -> State:
        return internal_state[2]
