from typing import ClassVar

from game.core.action import Action
from game.core.level import Level
from game.core.state import State


class BloxorzGame:
    COORDS_DELTAS: ClassVar[dict[Action, tuple[int, int]]] = {
        Action.UP: (-1, 0),
        Action.DOWN: (1, 0),
        Action.LEFT: (0, -1),
        Action.RIGHT: (0, 1),
    }

    def __init__(self, level: Level) -> None:
        self.level = level

    def start_state(self) -> State:
        start_coords = self.level.get_start()
        start_state = State(start_coords, start_coords)

        return start_state

    def is_goal(self, state: State) -> bool:
        goal_coords = self.level.get_goal()

        return state.is_standing() and state.get_first_coords() == goal_coords

    def successors(self, state: State) -> list[State]:
        ACTIONS = [Action.UP, Action.DOWN, Action.LEFT, Action.RIGHT]
        successors = []

        for action in ACTIONS:
            move_result = self.move_and_check_validity(state, action)

            if move_result is not None:
                successors.append(move_result)

        return successors

    def move_and_check_validity(self, state: State, action: Action) -> State | None:
        new_state = self.move(state, action)

        if self.is_valid_state(new_state):
            return new_state
        return None

    def move(self, state: State, action: Action) -> State:
        if state.is_standing():
            return self.roll_when_standing(state, action)

        delta_row, delta_col = self.COORDS_DELTAS[action]

        rolling_lengthwise = (state.is_lying_horizontally() and delta_col != 0) or (
            state.is_lying_vertically() and delta_row != 0
        )

        if rolling_lengthwise:
            return self.roll_lengthwise(state, action)
        return self.roll_sideways(state, action)

    def roll_when_standing(self, state: State, action: Action) -> State:
        delta_row, delta_col = self.COORDS_DELTAS[action]
        row1, col1 = state.coord1
        row2, col2 = state.coord2

        return State(
            (row1 + delta_row, col1 + delta_col),
            (row2 + delta_row * 2, col2 + delta_col * 2),
        )

    def roll_lengthwise(self, state: State, action: Action) -> State:
        delta_row, delta_col = self.COORDS_DELTAS[action]
        row1, col1 = state.coord1
        row2, col2 = state.coord2

        rolling_right_or_down = delta_row + delta_col > 0

        if rolling_right_or_down:
            new_row, new_col = (row2 + delta_row, col2 + delta_col)
        else:
            new_row, new_col = row1 + delta_row, col1 + delta_col
        return State((new_row, new_col), (new_row, new_col))

    def roll_sideways(self, state: State, action: Action) -> State:
        delta_row, delta_col = self.COORDS_DELTAS[action]
        row1, col1 = state.coord1
        row2, col2 = state.coord2

        return State(
            (row1 + delta_row, col1 + delta_col), (row2 + delta_row, col2 + delta_col)
        )

    def is_valid_state(self, state: State) -> bool:
        is_valid_coords1 = self.level.is_valid_tile(state.get_first_coords())
        is_valid_coords2 = self.level.is_valid_tile(state.get_second_coords())

        return is_valid_coords1 and is_valid_coords2
