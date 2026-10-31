from abc import ABC, abstractmethod

from src.game.core.level import Level
from src.game.core.state import State


class CostCalculator(ABC):
    def __init__(self, level: Level) -> None:
        self.level = level

    @abstractmethod
    def calculate_cost(self, current_state: State, next_state: State) -> float:
        pass
