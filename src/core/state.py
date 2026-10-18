"""Immutable, hashable dynamic state (used by solvers + GUI)."""

from __future__ import annotations

from dataclasses import dataclass

Coord = tuple[int, int]


@dataclass(frozen=True)
class State:
    # For normal block: a/b are the occupied cells (a == b when standing).
    # For split mode: a/b are the two cube positions.
    a: Coord
    b: Coord
    split: bool = False
    active: int = 0  # 0/1, only meaningful when split
    bridges: tuple[bool, ...] = ()

    def __post_init__(self) -> None:
        # Normalize non-split ordering so (b,a) == (a,b).
        if not self.split and self.a > self.b:
            a, b = self.a, self.b
            object.__setattr__(self, "a", b)
            object.__setattr__(self, "b", a)
        if self.active not in (0, 1):
            raise ValueError("active must be 0 or 1")

    @staticmethod
    def standing(r: int, c: int, bridges: tuple[bool, ...] = ()) -> "State":
        return State(a=(r, c), b=(r, c), split=False, active=0, bridges=bridges)

    @staticmethod
    def block(a: Coord, b: Coord, bridges: tuple[bool, ...] = ()) -> "State":
        return State(a=a, b=b, split=False, active=0, bridges=bridges)

    @staticmethod
    def split_state(a: Coord, b: Coord, active: int,
                    bridges: tuple[bool, ...] = ()) -> "State":
        if a == b:
            raise ValueError("split cubes must be on distinct cells")
        return State(a=a, b=b, split=True, active=active, bridges=bridges)

    def is_standing(self) -> bool:
        return not self.split and self.a == self.b

    def orientation(self) -> str:
        if self.split:
            return "SPLIT"
        if self.a == self.b:
            return "STANDING"
        if self.a[0] == self.b[0]:
            return "LYING_H"
        return "LYING_V"

    def occupied(self) -> tuple[Coord, ...]:
        if self.is_standing():
            return (self.a,)
        return (self.a, self.b)

    def active_pos(self) -> Coord:
        return self.a if self.active == 0 else self.b

    def key(self) -> tuple:
        # Explicit key for visited sets (frozen dataclass is already hashable,
        # but this makes the components obvious for the report).
        return (self.a, self.b, self.split, self.active, self.bridges)
