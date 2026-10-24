import heapq
import itertools

from src.game.core.action import Action
from src.game.core.coordinate import Coordinate
from src.game.core.level import Level
from src.game.core.state import State
from src.game.logic.state_mover import StateMover
from src.solver_algorithms.heuristic.calculators.grid_distance_heuristic_calculator import (
    GridDistanceHeuristicCalculator,
)

Pose = tuple[Coordinate, Coordinate]

_ROLLS = (Action.UP, Action.DOWN, Action.LEFT, Action.RIGHT)


class RelaxedBlockHeuristicCalculator(GridDistanceHeuristicCalculator):
    """Exact number of rolls of the whole 1x1x2 block in an easier version of the game.

    The relaxed game uses the same rolling rules (StateMover from the engine) but:
      - every bridge is always open and switches do nothing,
      - the block may stand on fragile tiles,
      - rolling onto a split switch may either teleport (as in the real game) or
        simply continue rolling.
    Every real path of the whole block is also a path of the relaxed game, so its
    exact remaining number of actions is a lower bound of the real one.

    It is computed once per level with a backward multi-source Dijkstra over all
    block poses: the goal pose has value 0, and standing on a split switch p has the
    value of the split state right after the teleport (GRID_DISTANCE bound, at least
    2). Split states themselves use the GRID_DISTANCE heuristic.

    Admissible and consistent for any cost function with every cost >= 1: it is an
    exact distance in a relaxed graph whose every edge costs 1 <= the real cost.
    """

    def __init__(self, level: Level) -> None:
        super().__init__(level)

        self.relaxed_distances = self._calculate_relaxed_distances()

    def calculate_heuristic(self, state: State) -> float:
        if state.is_split():
            return super().calculate_heuristic(state)

        pose = (state.get_first_coords(), state.get_second_coords())
        return self.relaxed_distances.get(pose, super().calculate_heuristic(state))

    def _calculate_relaxed_distances(self) -> dict[Pose, float]:
        predecessors = self._build_reversed_pose_graph()

        distances: dict[Pose, float] = {(self.goal, self.goal): 0}
        for switch, _ in self.split_switches:
            after_teleport = max(self.after_teleport[switch], 2)
            distances[(switch, switch)] = min(
                distances.get((switch, switch), after_teleport), after_teleport
            )

        counter = itertools.count()
        queue = [
            (distance, next(counter), pose) for pose, distance in distances.items()
        ]
        heapq.heapify(queue)

        while queue:
            distance, _, pose = heapq.heappop(queue)
            if distance > distances[pose]:
                continue
            for previous_pose in predecessors.get(pose, ()):
                if distance + 1 < distances.get(previous_pose, float("inf")):
                    distances[previous_pose] = distance + 1
                    heapq.heappush(queue, (distance + 1, next(counter), previous_pose))

        return distances

    def _build_reversed_pose_graph(self) -> dict[Pose, list[Pose]]:
        predecessors: dict[Pose, list[Pose]] = {}

        for pose in self._get_all_poses():
            block = State(pose[0], pose[1], {}, False, None)
            for action in _ROLLS:
                next_block = StateMover.act(block, action)
                next_pose = (
                    next_block.get_first_coords(),
                    next_block.get_second_coords(),
                )
                if all(self.level.is_tile(coords) for coords in next_pose):
                    predecessors.setdefault(next_pose, []).append(pose)

        return predecessors

    def _get_all_poses(self) -> list[Pose]:
        poses = []

        for row, col in self.level.get_map():
            poses.append(((row, col), (row, col)))
            for neighbour in ((row, col + 1), (row + 1, col)):
                if self.level.is_tile(neighbour):
                    poses.append(((row, col), neighbour))

        return poses
