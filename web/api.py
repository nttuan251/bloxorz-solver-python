from __future__ import annotations

import re
from collections import Counter
from functools import lru_cache
from pathlib import Path
from typing import Any

from src.game.core.action import Action
from src.game.core.level import Level
from src.game.core.state import State
from src.game.logic.engine import BloxorzGame
from src.game.logic.level_loader import LevelLoader
from src.game.logic.state_mover import StateMover
from src.solver_algorithms.core.cost_calculator_type import CostCalculatorType
from src.solver_algorithms.core.heuristic_calculator_type import HeuristicCalculatorType
from src.solver_algorithms.core.solver_type import SolverType
from src.solver_algorithms.solver_runner import SolverRunner

MAPS_DIR = Path(__file__).resolve().parent.parent / "maps"
LEVEL_FILE = re.compile(r"^level_(\d+)\.json$")

# UCS has no SolverType of its own: it is A* with the zero heuristic.
SOLVERS: dict[str, tuple[SolverType, bool, bool]] = {
    # name: (solver type, uses cost, uses heuristic)
    "BFS": (SolverType.BFS, False, False),
    "DFS": (SolverType.DFS, False, False),
    "UCS": (SolverType.A_STAR, True, False),
    "A*": (SolverType.A_STAR, True, True),
}


class ApiError(ValueError):
    """Bad input from the client; the server turns it into a 400 response."""


# ---------- levels ----------


def list_levels() -> list[dict[str, Any]]:
    levels = []
    for path in sorted(MAPS_DIR.glob("level_*.json")):
        match = LEVEL_FILE.match(path.name)
        if match:
            levels.append({"id": path.stem, "number": int(match.group(1))})
    return sorted(levels, key=lambda lv: lv["number"])


def _level_path(level_id: str) -> Path:
    if not LEVEL_FILE.match(f"{level_id}.json"):
        raise ApiError(f"Unknown level id: {level_id!r}")
    path = MAPS_DIR / f"{level_id}.json"
    if not path.is_file():
        raise ApiError(f"Level file not found: {path.name}")
    return path


@lru_cache(maxsize=64)
def _load(level_id: str) -> tuple[Level, BloxorzGame]:
    level = LevelLoader.parse_level_from_file(str(_level_path(level_id)))
    return level, BloxorzGame(level)


def level_payload(level_id: str) -> dict[str, Any]:
    level, game = _load(level_id)
    tiles = [
        {"r": r, "c": c, "type": tile.value} for (r, c), tile in level.get_map().items()
    ]
    switches = []
    for (r, c), targets in level.switches.items():
        switches.append(
            {
                "r": r,
                "c": c,
                "type": level.get_map()[(r, c)].value,
                "targets": [
                    {"r": tr, "c": tc, "action": act.value} for (tr, tc), act in targets
                ],
            }
        )
    rows = max(r for r, _ in level.get_map()) + 1
    cols = max(c for _, c in level.get_map()) + 1
    return {
        "id": level_id,
        "rows": rows,
        "cols": cols,
        "tiles": tiles,
        "switches": switches,
        "start": list(level.get_start()),
        "goal": list(level.get_goal()),
        "state": state_to_json(game.start_state()),
    }


# ---------- state (de)serialization ----------


def state_to_json(state: State) -> dict[str, Any]:
    controlled = state.get_controlled_cube_coords()
    return {
        "a": list(state.get_first_coords()),
        "b": list(state.get_second_coords()),
        "bridges": [
            [r, c, is_open]
            for (r, c), is_open in sorted(state.get_bridges_open_states().items())
        ],
        "split": state.is_split(),
        "active": list(controlled) if controlled is not None else None,
    }


def _coord(value: Any) -> tuple[int, int]:
    if not (
        isinstance(value, list)
        and len(value) == 2
        and all(isinstance(v, int) for v in value)
    ):
        raise ApiError(f"Expected [row, col], got {value!r}")
    return value[0], value[1]


def state_from_json(data: Any) -> State:
    if not isinstance(data, dict):
        raise ApiError("State must be an object")
    try:
        bridges = {(r, c): bool(is_open) for r, c, is_open in data.get("bridges", [])}
        split = bool(data.get("split", False))
        active = _coord(data["active"]) if data.get("active") is not None else None
        return State(_coord(data["a"]), _coord(data["b"]), bridges, split, active)
    except (KeyError, TypeError, AssertionError) as exc:
        raise ApiError(f"Invalid state: {exc}") from exc


def _action(name: Any) -> Action:
    try:
        return Action(name)
    except ValueError as exc:
        raise ApiError(f"Unknown action: {name!r}") from exc


# ---------- playing ----------


def _failure_reason(level: Level, attempted: State) -> str:
    """Why a move was rejected, so the GUI can show the right animation."""
    bridges = attempted.get_bridges_open_states()
    for coords in (attempted.get_first_coords(), attempted.get_second_coords()):
        if not level.is_valid_tile(coords, bridges):
            return "fall"
    if attempted.is_standing() and level.is_fragile_tile(attempted.get_first_coords()):
        return "fragile"
    if (
        attempted.is_split()
        and attempted.get_first_coords() == attempted.get_second_coords()
    ):
        return "blocked"
    return "fall"


def step(level_id: str, state_data: Any, action_name: Any) -> dict[str, Any]:
    level, game = _load(level_id)
    state = state_from_json(state_data)
    action = _action(action_name)
    if action == Action.SWITCH_CONTROL and not state.is_split():
        raise ApiError("SWITCH_CONTROL is only allowed while the block is split")
    # a state from another level (e.g. a stale request after switching levels) has other bridges
    expected = {(r, c) for r, c, _ in level_payload(level_id)["state"]["bridges"]}
    if {(r, c) for r, c, _ in state_data["bridges"]} != expected:
        raise ApiError(f"This state does not belong to {level_id}")

    # `moved` is the pose right after rolling, before switches, merges and teleports.
    moved = StateMover.act(state, action)
    result = game.state_manager.act_and_activate_triggers(state, action)

    if result is None:
        return {
            "ok": False,
            "reason": _failure_reason(level, moved),
            "moved": state_to_json(moved),
        }
    return {
        "ok": True,
        "moved": state_to_json(moved),
        "state": state_to_json(result),
        "won": game.is_goal(result),
    }


# ---------- solving ----------


def options() -> dict[str, Any]:
    return {
        "solvers": [
            {"name": name, "usesCost": uses_cost, "usesHeuristic": uses_h}
            for name, (_, uses_cost, uses_h) in SOLVERS.items()
        ],
        "costs": [c.value for c in CostCalculatorType],
        "heuristics": [
            h.value
            for h in HeuristicCalculatorType
            if h != HeuristicCalculatorType.TRIVIAL
        ],
    }


def _enum(enum_type: Any, value: Any, default: Any) -> Any:
    if value is None:
        return default
    try:
        return enum_type(value)
    except ValueError as exc:
        raise ApiError(f"Unknown {enum_type.__name__}: {value!r}") from exc


def solve(
    level_id: str, solver_name: Any, cost: Any = None, heuristic: Any = None
) -> dict[str, Any]:
    """Solve from the level's start state and return the path plus search metrics.

    `explored` counts, for every tile, how many expanded states had a block or cube on it.
    """
    if solver_name not in SOLVERS:
        raise ApiError(f"Unknown solver: {solver_name!r}")
    solver_type, uses_cost, uses_heuristic = SOLVERS[solver_name]

    cost_type = (
        _enum(CostCalculatorType, cost, CostCalculatorType.UNIFORM)
        if uses_cost
        else None
    )
    if uses_heuristic:
        heuristic_type = _enum(
            HeuristicCalculatorType, heuristic, HeuristicCalculatorType.TELEPORT_AWARE
        )
    elif uses_cost:
        heuristic_type = HeuristicCalculatorType.TRIVIAL
    else:
        heuristic_type = None

    runner = SolverRunner(
        solver_type, str(_level_path(level_id)), cost_type, heuristic_type
    )
    metrics = runner.solve_for_metrics()
    actions, path_cost = metrics.solution

    _, game = _load(level_id)
    states = [game.start_state()]
    for action in actions:
        nxt = game.state_manager.act_and_activate_triggers(states[-1], action)
        if nxt is None:  # should never happen: the solver only uses legal moves
            raise RuntimeError(f"Solver returned an illegal move: {action}")
        states.append(nxt)

    heat: Counter[tuple[int, int]] = Counter()
    for visited in runner.solver.visited:
        heat[visited.get_first_coords()] += 1
        if visited.get_second_coords() != visited.get_first_coords():
            heat[visited.get_second_coords()] += 1

    return {
        "level": level_id,
        "solver": solver_name,
        "cost": cost_type.value if cost_type else None,
        "heuristic": heuristic_type.value
        if uses_heuristic and heuristic_type
        else None,
        "found": bool(actions) or game.is_goal(game.start_state()),
        "actions": [a.value for a in actions],
        "states": [state_to_json(s) for s in states],
        "metrics": {
            "steps": metrics.solution_length,
            "pathCost": path_cost,
            "expanded": metrics.expanded_notes,
            "timeMs": round(metrics.search_time_in_secs * 1000, 2),
            "memoryMb": round(metrics.peak_memory_in_mb, 3),
        },
        "explored": [[r, c, n] for (r, c), n in heat.items()],
    }
