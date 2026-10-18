"""Immutable level definition (static part of the game)."""

from __future__ import annotations

from dataclasses import dataclass, field

from .tile import BridgeMode, SwitchKind

Coord = tuple[int, int]


@dataclass(frozen=True)
class BridgeGroup:
    bid: str
    cells: tuple[Coord, ...]
    init_open: bool = False  # default closed (agreed)


@dataclass(frozen=True)
class Switch:
    pos: Coord
    kind: SwitchKind
    targets: tuple[str, ...] = ()
    mode: BridgeMode = BridgeMode.TOGGLE
    # Only for SPLIT kind:
    split_a: Coord | None = None
    split_b: Coord | None = None


@dataclass(frozen=True)
class Level:
    rows: int
    cols: int
    start: Coord
    goal: Coord
    # Original grid chars (padded), kept for GUI rendering.
    grid: tuple[tuple[str, ...], ...]
    fragile: frozenset[Coord] = frozenset()
    # (r,c) -> bridge id
    bridge_at: dict[Coord, str] = field(default_factory=dict, compare=False)
    bridge_groups: dict[str, BridgeGroup] = field(default_factory=dict, compare=False)
    bridge_order: tuple[str, ...] = ()
    switches: tuple[Switch, ...] = ()
    switch_at: dict[Coord, Switch] = field(default_factory=dict, compare=False)

    def initial_mask(self) -> tuple[bool, ...]:
        return tuple(self.bridge_groups[bid].init_open for bid in self.bridge_order)
