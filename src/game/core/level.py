from collections import deque

from src.game.core.coordinate import Coordinate
from src.game.core.switch import SwitchActionType
from src.game.core.tile import TileType


class Level:
    def __init__(
        self,
        map: dict[Coordinate, TileType],
        bridges_open_default_states: dict[Coordinate, bool],
        switches: dict[Coordinate, list[tuple[Coordinate, SwitchActionType]]],
    ) -> None:
        starts = [coords for coords, tile in map.items() if tile == TileType.START]
        goals = [coords for coords, tile in map.items() if tile == TileType.GOAL]

        if len(starts) != 1 or len(goals) != 1:
            raise ValueError("Each map needs exactly one start and one goal.")

        self.map = map.copy()
        self.start = starts[0]
        self.goal = goals[0]
        self.bridges_open_default_states = bridges_open_default_states.copy()
        self.switches = switches.copy()

    def get_start(self) -> Coordinate:
        return self.start

    def get_map(self) -> dict[Coordinate, TileType]:
        return self.map

    def get_goal(self) -> Coordinate:
        return self.goal

    def get_bridges_open_default_states(self) -> dict[Coordinate, bool]:
        return self.bridges_open_default_states

    def is_valid_tile(
        self, coords: Coordinate, bridges_open_states: dict[Coordinate, bool]
    ) -> bool:
        is_void = self.map.get(coords) is None
        is_closed_bridge = bridges_open_states.get(coords) is False

        return not is_void and not is_closed_bridge

    def is_switch(self, coords: Coordinate) -> bool:
        return (
            self.is_soft_switch(coords)
            or self.is_heavy_switch(coords)
            or self.is_split_switch(coords)
        )

    def is_soft_switch(self, coords: Coordinate) -> bool:
        return self.map.get(coords) == TileType.SOFT_SWITCH

    def is_heavy_switch(self, coords: Coordinate) -> bool:
        return self.map.get(coords) == TileType.HEAVY_SWITCH

    def is_split_switch(self, coords: Coordinate) -> bool:
        return self.map.get(coords) == TileType.SPLIT_SWITCH

    def get_associated_coords_and_actions_from_switch(
        self, coords: Coordinate
    ) -> list[tuple[Coordinate, SwitchActionType]]:
        if not self.is_switch(coords):
            raise ValueError("Provided coordinates do not correspond to a switch.")

        return self.switches[coords]

    def is_fragile_tile(self, coords: Coordinate) -> bool:
        return self.map.get(coords) == TileType.FRAGILE

    def get_split_switches(
        self,
    ) -> list[tuple[Coordinate, tuple[Coordinate, Coordinate]]]:
        split_switches = []

        for coords, tile in self.map.items():
            if tile == TileType.SPLIT_SWITCH:
                destinations = self.get_associated_coords_and_actions_from_switch(
                    coords
                )
                split_switches.append(
                    (coords, (destinations[0][0], destinations[1][0]))
                )

        return split_switches

    def has_tile(self, coords: Coordinate) -> bool:
        """True if the cell has any tile (bridges count, whether open or closed)."""
        return coords in self.map

    def get_tile_distances_from(self, source: Coordinate) -> dict[Coordinate, int]:
        """Fewest 4-neighbour steps from source to every tile, walking only on tiles
        and treating every bridge as open. Tiles that cannot be reached are absent."""
        distances = {source: 0}
        queue = deque([source])

        while queue:
            row, col = queue.popleft()
            for neighbour in ((row - 1, col), (row + 1, col), (row, col - 1), (row, col + 1)):
                if self.has_tile(neighbour) and neighbour not in distances:
                    distances[neighbour] = distances[(row, col)] + 1
                    queue.append(neighbour)

        return distances
