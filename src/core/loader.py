"""TXT level loader (grid + optional footer).

Grid symbols (see maps/MAP_FORMAT.txt):
    - / space : void
    o / .     : normal floor ('.' kept as alias for legacy maps)
    S         : start (also floor)
    T         : goal (support like floor, win only when standing)
    f         : fragile (standing/single-cube -> fall, lying -> safe)
    b         : bridge cell (passable iff its group is open, default closed)
    s         : soft switch (any press)
    h         : heavy switch (standing only, no single-cube)
    p         : split switch (standing only -> teleport + split)
    A / B     : split destinations (also floor)

Footer (optional, after a blank line):
    [BRIDGES]
    b0: (r,c) (r,c) init=closed
    [SWITCHES]
    soft (r,c) -> b0,b1 toggle
    heavy (r,c) -> b0 open
    split (r,c) -> A=(ra,ca) B=(rb,cb) [bridges=b0,b1 mode=toggle]
"""

from __future__ import annotations

import re
from pathlib import Path

from .level import BridgeGroup, Level, Switch
from .tile import BridgeMode, SwitchKind

_TUPLE = re.compile(r"\(\s*(\d+)\s*,\s*(\d+)\s*\)")
_BID = re.compile(r"\bb\d+\b")


def _parse_coords(text: str) -> list[tuple[int, int]]:
    return [(int(r), int(c)) for r, c in _TUPLE.findall(text)]


def _parse_mode(text: str, default: BridgeMode = BridgeMode.TOGGLE) -> BridgeMode:
    t = text.lower()
    if "toggle" in t:
        return BridgeMode.TOGGLE
    if "open" in t or "permanent" in t or " on" in f" {t}":
        # 'permanent' without explicit target defaults to open.
        if "closed" in t or "off" in t:
            return BridgeMode.CLOSED
        return BridgeMode.OPEN
    if "closed" in t or "off" in t:
        return BridgeMode.CLOSED
    return default


def load_level(path: str | Path) -> Level:
    raw = Path(path).read_text(encoding="utf-8").splitlines()
    # Split grid vs footer: footer starts at first line beginning with '['.
    grid_lines: list[str] = []
    footer_lines: list[str] = []
    in_footer = False
    for line in raw:
        s = line.strip()
        if not in_footer and s.startswith("["):
            in_footer = True
        (footer_lines if in_footer else grid_lines).append(line)
    # Drop trailing empty grid lines (separator before footer).
    while grid_lines and grid_lines[-1].strip() == "":
        grid_lines.pop()

    if not grid_lines:
        raise ValueError(f"Empty level file: {path}")

    cols = max(len(line.rstrip("\n")) for line in grid_lines)
    # Pad ragged rows with void.
    grid: list[list[str]] = []
    for line in grid_lines:
        row = list(line.rstrip("\n"))
        row += ["-"] * (cols - len(row))
        grid.append(row)
    rows = len(grid)

    start: tuple[int, int] | None = None
    goal: tuple[int, int] | None = None
    fragile: set[tuple[int, int]] = set()
    b_cells: list[tuple[int, int]] = []
    soft_pos: list[tuple[int, int]] = []
    heavy_pos: list[tuple[int, int]] = []
    split_pos: list[tuple[int, int]] = []
    dest_a: tuple[int, int] | None = None
    dest_b: tuple[int, int] | None = None

    for r in range(rows):
        for c in range(cols):
            ch = grid[r][c]
            if ch == "S":
                if start is None:
                    start = (r, c)
            elif ch == "T":
                if goal is None:
                    goal = (r, c)
            elif ch == "f":
                fragile.add((r, c))
            elif ch == "b":
                b_cells.append((r, c))
            elif ch == "s":
                soft_pos.append((r, c))
            elif ch == "h":
                heavy_pos.append((r, c))
            elif ch == "p":
                split_pos.append((r, c))
            elif ch == "A":
                dest_a = (r, c)
            elif ch == "B":
                dest_b = (r, c)
            # 'o', '.', ' ', '-' need no set.

    if start is None:
        raise ValueError(f"Level {path} missing start 'S'")
    if goal is None:
        raise ValueError(f"Level {path} missing goal 'T'")

    # ---- footer parsing ----
    bridge_groups: dict[str, BridgeGroup] = {}
    switch_defs: list[Switch] = []
    section = ""
    for line in footer_lines:
        s = line.strip()
        if not s or s.startswith("#"):
            continue
        low = s.lower()
        if low.startswith("[bridges]"):
            section = "bridges"
            continue
        if low.startswith("[switches]"):
            section = "switches"
            continue
        if s.startswith("["):
            section = ""
            continue
        if section == "bridges":
            # e.g. "b0: (1,2) (1,3) init=closed"
            m = re.match(r"\s*(b\d+)\s*:?\s*(.*)", s, re.IGNORECASE)
            if not m:
                continue
            bid = m.group(1).lower()
            rest = m.group(2)
            cells = _parse_coords(rest)
            init_open = "open" in rest.lower() and "closed" not in rest.lower()
            # 'init=open' wins over bare 'open' check above only if explicit.
            if "init=open" in rest.lower():
                init_open = True
            if "init=closed" in rest.lower():
                init_open = False
            bridge_groups[bid] = BridgeGroup(bid=bid, cells=tuple(cells),
                                            init_open=init_open)
        elif section == "switches":
            switch_defs.append(_parse_switch_line(s, dest_a, dest_b))

    # Infer bridge group if grid has 'b' but no footer.
    if b_cells and not bridge_groups:
        bridge_groups["b0"] = BridgeGroup(bid="b0", cells=tuple(b_cells),
                                          init_open=False)
    # If footer defines groups, trust footer; also map any stray 'b'
    # not listed into b0 (tolerant).
    if bridge_groups and b_cells:
        listed = {cell for g in bridge_groups.values() for cell in g.cells}
        stray = [cell for cell in b_cells if cell not in listed]
        if stray:
            if "b0" in bridge_groups:
                old = bridge_groups["b0"]
                bridge_groups["b0"] = BridgeGroup(
                    bid="b0", cells=tuple(list(old.cells) + stray),
                    init_open=old.init_open)
            else:
                bridge_groups["b0"] = BridgeGroup(bid="b0",
                                                  cells=tuple(stray),
                                                  init_open=False)

    # Infer switches with no footer (no-op links) so GUI can render them.
    if not switch_defs:
        for pos in soft_pos:
            switch_defs.append(Switch(pos=pos, kind=SwitchKind.SOFT))
        for pos in heavy_pos:
            switch_defs.append(Switch(pos=pos, kind=SwitchKind.HEAVY))
        for pos in split_pos:
            a = dest_a or pos
            b = dest_b or pos
            switch_defs.append(Switch(pos=pos, kind=SwitchKind.SPLIT,
                                      split_a=a, split_b=b))

    bridge_order = tuple(sorted(bridge_groups.keys()))
    bridge_at: dict[tuple[int, int], str] = {}
    for bid in bridge_order:
        for cell in bridge_groups[bid].cells:
            bridge_at[cell] = bid
    switch_at = {sw.pos: sw for sw in switch_defs}

    grid_t = tuple(tuple(row) for row in grid)
    return Level(rows=rows, cols=cols, start=start, goal=goal, grid=grid_t,
                 fragile=frozenset(fragile), bridge_at=bridge_at,
                 bridge_groups=bridge_groups, bridge_order=bridge_order,
                 switches=tuple(switch_defs), switch_at=switch_at)


def _parse_switch_line(s: str, dest_a, dest_b) -> Switch:
    low = s.lower()
    if low.startswith("soft"):
        kind = SwitchKind.SOFT
    elif low.startswith("heavy"):
        kind = SwitchKind.HEAVY
    elif low.startswith("split"):
        kind = SwitchKind.SPLIT
    else:
        raise ValueError(f"Bad switch line: {s!r}")

    coords = _parse_coords(s)
    if not coords:
        raise ValueError(f"Switch line missing (r,c): {s!r}")
    pos = coords[0]
    bids = tuple(_BID.findall(low))
    mode = _parse_mode(s, default=BridgeMode.TOGGLE)
    # Permanent without explicit open/closed defaults to open.
    if "permanent" in low and "toggle" not in low \
            and "open" not in low and "closed" not in low:
        mode = BridgeMode.OPEN

    if kind in (SwitchKind.SOFT, SwitchKind.HEAVY):
        return Switch(pos=pos, kind=kind, targets=bids, mode=mode)

    # SPLIT: coords[1], coords[2] are destinations if given as (r,c).
    a = b = None
    if len(coords) >= 3:
        a, b = coords[1], coords[2]
    elif "a" in low and "b" in low and dest_a and dest_b:
        a, b = dest_a, dest_b
    elif dest_a and dest_b:
        a, b = dest_a, dest_b
    elif len(coords) == 2:
        # Only one dest given; duplicate is invalid -> fall back to pos.
        a, b = coords[1], coords[1]
    else:
        a, b = pos, pos
    return Switch(pos=pos, kind=kind, targets=bids, mode=mode,
                  split_a=a, split_b=b)
