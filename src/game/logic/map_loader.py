from pathlib import Path
from typing import ClassVar

from game.core.coordinate import Coordinate
from game.core.level import Level
from game.core.tile import TileType


class MapLoader:
    CHARACTER_TILE_TYPE_MAP: ClassVar[dict[str, TileType]] = {
        "o": TileType.NORMAL,
        "S": TileType.START,
        "T": TileType.GOAL,
    }

    @classmethod
    def parse_level_from_file(cls, file_location: str) -> Level:
        map_data = cls.read_data_from_file(file_location)
        return cls.build_level_from_raw_string(map_data)

    @classmethod
    def read_data_from_file(cls, file_location: str) -> str:
        return Path(file_location).read_text(encoding="utf-8")

    @classmethod
    def build_level_from_raw_string(cls, map_data: str) -> Level:
        tiles_map: dict[Coordinate, TileType] = {}
        grid_lines = map_data.splitlines()

        for row_index, line in enumerate(grid_lines):
            for col_index, character in enumerate(line):
                current_coords = (row_index, col_index)

                current_tile_type = cls.CHARACTER_TILE_TYPE_MAP.get(character)

                if current_tile_type is None:
                    raise ValueError("Invalid character encountered.")

                tiles_map[current_coords] = current_tile_type

        return Level(tiles_map)
