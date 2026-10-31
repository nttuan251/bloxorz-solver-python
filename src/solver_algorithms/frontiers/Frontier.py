from abc import ABC, abstractmethod

from src.game.core.state import State


class Frontier(ABC):
    @abstractmethod
    def contains(self, state: State) -> bool:
        pass

    @abstractmethod
    def push(self, state: State, priority: float) -> None:
        pass

    @abstractmethod
    def pop(self) -> State | None:
        pass
