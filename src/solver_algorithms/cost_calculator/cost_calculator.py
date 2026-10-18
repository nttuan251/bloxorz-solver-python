from abc import ABC, abstractmethod

from game.core.level import Level
from game.core.state import State


class CostCalculator(ABC):
    def __init__(self, level: Level) -> None:
        self.level = level

    @abstractmethod
    def calculate_cost(self, current_state: State, next_state: State) -> float:
        pass
