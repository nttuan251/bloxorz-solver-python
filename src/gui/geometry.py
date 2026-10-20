from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import TYPE_CHECKING

from src.game.core.action import Action

if TYPE_CHECKING:
    from src.game.core.state import State

Coordinate = tuple[int, int]
Vec3Tuple = tuple[float, float, float]


class Orientation(str, Enum):
    STANDING = "STANDING"
    LYING_H = "LYING_H"
    LYING_V = "LYING_V"


_POSE_TRANSITIONS: dict[Orientation, dict[Action, tuple[int, int, Orientation]]] = {
    Orientation.STANDING: {
        Action.RIGHT: (0, 1, Orientation.LYING_H),
        Action.LEFT: (0, -2, Orientation.LYING_H),
        Action.UP: (-2, 0, Orientation.LYING_V),
        Action.DOWN: (1, 0, Orientation.LYING_V),
    },
    Orientation.LYING_H: {
        Action.RIGHT: (0, 2, Orientation.STANDING),
        Action.LEFT: (0, -1, Orientation.STANDING),
        Action.UP: (-1, 0, Orientation.LYING_H),
        Action.DOWN: (1, 0, Orientation.LYING_H),
    },
    Orientation.LYING_V: {
        Action.RIGHT: (0, 1, Orientation.LYING_V),
        Action.LEFT: (0, -1, Orientation.LYING_V),
        Action.UP: (-1, 0, Orientation.STANDING),
        Action.DOWN: (2, 0, Orientation.STANDING),
    },
}

DIRECTION_DELTAS: dict[Action, Coordinate] = {
    Action.UP: (-1, 0),
    Action.DOWN: (1, 0),
    Action.LEFT: (0, -1),
    Action.RIGHT: (0, 1),
}


@dataclass(frozen=True)
class BlockPose:
    row: int
    col: int
    orientation: Orientation

    @classmethod
    def from_state(cls, state: State) -> BlockPose:
        r1, c1 = state.get_first_coords()
        r2, c2 = state.get_second_coords()
        if state.is_lying_horizontally():
            return cls(r1, min(c1, c2), Orientation.LYING_H)
        if state.is_lying_vertically():
            return cls(min(r1, r2), c1, Orientation.LYING_V)
        return cls(r1, c1, Orientation.STANDING)

    def after(self, action: Action) -> BlockPose:
        d_row, d_col, orientation = _POSE_TRANSITIONS[self.orientation][action]
        return BlockPose(self.row + d_row, self.col + d_col, orientation)

    def roll_pivot(self, action: Action) -> tuple[Vec3Tuple, Vec3Tuple]:
        r, c = self.row, self.col
        if self.orientation is Orientation.STANDING:
            table = {
                Action.RIGHT: ((c + 0.5, 0, -r), (0, 0, 90)),
                Action.LEFT: ((c - 0.5, 0, -r), (0, 0, -90)),
                Action.UP: ((c, 0, -r + 0.5), (90, 0, 0)),
                Action.DOWN: ((c, 0, -r - 0.5), (-90, 0, 0)),
            }
        elif self.orientation is Orientation.LYING_H:
            table = {
                Action.RIGHT: ((c + 1.5, 0, -r), (0, 0, 90)),
                Action.LEFT: ((c - 0.5, 0, -r), (0, 0, -90)),
                Action.UP: ((c + 0.5, 0, -r + 0.5), (90, 0, 0)),
                Action.DOWN: ((c + 0.5, 0, -r - 0.5), (-90, 0, 0)),
            }
        else:
            table = {
                Action.RIGHT: ((c + 0.5, 0, -(r + 0.5)), (0, 0, 90)),
                Action.LEFT: ((c - 0.5, 0, -(r + 0.5)), (0, 0, -90)),
                Action.UP: ((c, 0, -r + 0.5), (90, 0, 0)),
                Action.DOWN: ((c, 0, -(r + 1.5)), (-90, 0, 0)),
            }
        return table[action]
