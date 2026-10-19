import json
from pathlib import Path
from typing import ClassVar

from src.game.core.coordinate import Coordinate
from src.game.core.level import Level
from src.game.core.switch import SwitchActionType
from src.game.core.tile import TileType


class LevelLoader:
    CHARACTER_TILE_TYPE_MAP: ClassVar[dict[str, TileType]] = {
        "o": TileType.NORMAL,
        ".": TileType.NORMAL,
        "S": TileType.START,
        "T": TileType.GOAL,
        "f": TileType.FRAGILE,
        "b": TileType.BRIDGE,
        "s": TileType.SOFT_SWITCH,
        "h": TileType.HEAVY_SWITCH,
        "p": TileType.SPLIT_SWITCH,
    }

    @classmethod
    def parse_level_from_file(cls, file_location: str) -> Level:
        level_data = cls._read_data_from_file(file_location)
        return cls._build_level_from_data(level_data)

    @classmethod
    def _read_data_from_file(cls, file_location: str) -> dict:
        data = json.loads(Path(file_location).read_text(encoding="utf-8"))

        # Loose check, specific types in the list are not validated
        assert isinstance(data, dict)
        assert isinstance(data.get("map"), list)
        assert isinstance(data.get("bridges"), list)
        assert isinstance(data.get("switches"), list)

        return data

    @classmethod
    def _build_level_from_data(cls, level_data: dict) -> Level:
        map = cls._build_map_from_data(level_data["map"])
        bridges = cls._build_bridges_from_data(level_data["bridges"])
        switches = cls._build_switches_from_data(level_data["switches"])

        return Level(map, bridges, switches)

    @classmethod
    def _build_map_from_data(cls, map_data: list[str]) -> dict[Coordinate, TileType]:
        level_map = {}
        for row_index, row in enumerate(map_data):
            for col_index, character in enumerate(row):
                if character in cls.CHARACTER_TILE_TYPE_MAP:
                    level_map[(row_index, col_index)] = cls.CHARACTER_TILE_TYPE_MAP[
                        character
                    ]
        return level_map

    @classmethod
    def _build_bridges_from_data(
        cls, bridges_data: list[dict]
    ) -> dict[Coordinate, bool]:
        bridges: dict[Coordinate, bool] = {}

        for bridge in bridges_data:
            coords = tuple(bridge["position"])
            initial_state = bridge["initial_state"]
            bridges[coords] = initial_state

        return bridges

    @classmethod
    def _build_switches_from_data(
        cls, switches_data: list[dict]
    ) -> dict[Coordinate, list[tuple[Coordinate, SwitchActionType]]]:
        switches: dict[Coordinate, list[tuple[Coordinate, SwitchActionType]]] = {}

        for switch in switches_data:
            coords: Coordinate = tuple(switch["position"])
            associated_coords_and_actions: list[tuple[Coordinate, SwitchActionType]] = [
                (tuple(bridge_coords), SwitchActionType(switch_action))
                for bridge_coords, switch_action in switch["coords_and_actions"]
            ]

            switches[coords] = associated_coords_and_actions

        return switches
