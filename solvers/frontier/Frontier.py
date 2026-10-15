from abc import ABC, abstractmethod

from core.state import state_type


class Frontier(ABC):
    @abstractmethod
    def contains(self, state: state_type) -> bool:
        pass

    @abstractmethod
    def push(self, state: state_type, current_min_cost: float | None = None) -> None:
        pass

    @abstractmethod
    def pop(self) -> state_type | None:
        pass
