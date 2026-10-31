from enum import Enum


class SolverType(str, Enum):
    DFS = "DFS"
    BFS = "BFS"
    A_STAR = "A_STAR"
