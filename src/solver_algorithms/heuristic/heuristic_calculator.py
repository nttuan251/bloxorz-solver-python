from abc import ABC, abstractmethod

from game.core.level import Level
from game.core.state import State


class HeuristicCalculator(ABC):
    def __init__(self, level: Level) -> None:
        self.level = level

    @abstractmethod
    def calculate_heuristic(self, state: State) -> float:
        pass
