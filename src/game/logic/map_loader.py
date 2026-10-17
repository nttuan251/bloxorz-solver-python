import json
from pathlib import Path
from typing import ClassVar

from game.core.coordinate import Coordinate
from game.core.level import Level
from game.core.switch import SwitchActionType
from game.core.tile import TileType


class MapLoader:
    CHARACTER_TILE_TYPE_MAP: ClassVar[dict[str, TileType]] = {
        "o": TileType.NORMAL,
        ".": TileType.NORMAL,
        "S": TileType.START,
        "T": TileType.GOAL,
        "f": TileType.FRAGILE,
        "b": TileType.BRIDGE,
        "s": TileType.SOFT_SWITCH,
        "h": TileType.HEAVY_SWITCH,
    }

    @classmethod
    def parse_level_from_file(cls, file_location: str) -> Level:
        level_data = cls.read_data_from_file(file_location)
        return cls.build_level_from_data(level_data)

    @classmethod
    def read_data_from_file(cls, file_location: str) -> dict:
        data = json.loads(Path(file_location).read_text(encoding="utf-8"))

        # Loose check, specific types in the list are not validated
        assert isinstance(data, dict)
        assert isinstance(data.get("map"), list)
        assert isinstance(data.get("bridges"), list)
        assert isinstance(data.get("switches"), list)

        return data

    @classmethod
    def build_level_from_data(cls, level_data: dict) -> Level:
        map = cls.build_map_from_data(level_data["map"])
        bridges = cls.build_bridges_from_data(level_data["bridges"])
        switches = cls.build_switches_from_data(level_data["switches"])

        return Level(map, bridges, switches)

    @classmethod
    def build_map_from_data(cls, map_data: list[str]) -> dict[Coordinate, TileType]:
        level_map = {}
        for row_index, row in enumerate(map_data):
            for col_index, character in enumerate(row):
                if character in cls.CHARACTER_TILE_TYPE_MAP:
                    level_map[(row_index, col_index)] = cls.CHARACTER_TILE_TYPE_MAP[
                        character
                    ]
        return level_map

    @classmethod
    def build_bridges_from_data(
        cls, bridges_data: list[dict]
    ) -> dict[Coordinate, bool]:
        bridges: dict[Coordinate, bool] = {}

        for bridge in bridges_data:
            coords = tuple(bridge["position"])
            initial_state = bridge["initial_state"]
            bridges[coords] = initial_state

        return bridges

    @classmethod
    def build_switches_from_data(
        cls, switches_data: list[dict]
    ) -> dict[Coordinate, tuple[list[Coordinate], SwitchActionType]]:
        switches: dict[Coordinate, tuple[list[Coordinate], SwitchActionType]] = {}

        for switch in switches_data:
            coords: Coordinate = tuple(switch["position"])
            associated_bridges: list[Coordinate] = [
                tuple(bridge_coords) for bridge_coords in switch["associated_bridges"]
            ]
            switch_action = SwitchActionType(switch["action"])

            switches[coords] = (associated_bridges, switch_action)

        return switches
