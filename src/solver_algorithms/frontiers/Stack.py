from collections import deque

from src.game.core.state import State
from src.solver_algorithms.frontiers.Frontier import Frontier


class Stack(Frontier):
    def __init__(self) -> None:
        super().__init__()
        self.data: deque[State] = deque()
        self.lookup_data: set[State] = set()

    def contains(self, state: State) -> bool:
        return state in self.lookup_data

    def push(self, state: State, priority: float) -> None:
        self.data.append(state)
        self.lookup_data.add(state)

    def pop(self) -> State | None:
        if len(self.data) == 0:
            return None

        state = self.data.pop()
        self.lookup_data.remove(state)
        return state
