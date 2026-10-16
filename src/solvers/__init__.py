"""Solver package: one function per algorithm, same signature."""

from .astar import solve_astar
from .base import Solution
from .bfs import solve_bfs
from .dfs import solve_dfs
from .ucs import solve_ucs

__all__ = ["solve_bfs", "solve_dfs", "solve_ucs", "solve_astar", "Solution"]

SOLVERS = {
    "bfs": solve_bfs,
    "dfs": solve_dfs,
    "ucs": solve_ucs,
    "astar": solve_astar,
}
