from collections import deque

from core.state import state_type

from solvers.frontier.Frontier import Frontier


class Stack(Frontier):
    def __init__(self) -> None:
        super().__init__()
        self.data: deque[state_type] = deque()
        self.lookup_data: set[state_type] = set()

    def contains(self, state: state_type) -> bool:
        return state in self.data

    def push(self, state: state_type, current_min_cost: float | None = None) -> None:
        self.data.append(state)
        self.lookup_data.add(state)

    def pop(self) -> state_type | None:
        if len(self.data) == 0:
            return None

        state = self.data.pop()
        self.lookup_data.remove(state)
        return state
