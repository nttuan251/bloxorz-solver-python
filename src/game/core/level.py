from game.core.coordinate import Coordinate
from game.core.tile import TileType


class Level:
    def __init__(self, map: dict[Coordinate, TileType]) -> None:
        starts = [coords for coords, tile in map.items() if tile == TileType.START]
        goals = [coords for coords, tile in map.items() if tile == TileType.GOAL]

        if len(starts) != 1 or len(goals) != 1:
            raise ValueError("Each map needs exactly one start and one goal.")

        self.map = map
        self.start = starts[0]
        self.goal = goals[0]

    def get_start(self) -> Coordinate:
        return self.start

    def get_goal(self) -> Coordinate:
        return self.goal

    def is_valid_tile(self, coords: Coordinate) -> bool:
        return self.map.get(coords) is not None
