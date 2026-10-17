from typing import ClassVar

from game.core.action import Action
from game.core.state import State


class StateMover:
    _COORDS_DELTAS: ClassVar[dict[Action, tuple[int, int]]] = {
        Action.UP: (-1, 0),
        Action.DOWN: (1, 0),
        Action.LEFT: (0, -1),
        Action.RIGHT: (0, 1),
    }

    @classmethod
    def act(cls, state: State, action: Action) -> State:
        if state.is_split():
            return cls._act_when_split(state, action)
        else:
            return cls._act_when_whole(state, action)

    @classmethod
    def _act_when_whole(cls, state: State, action: Action) -> State:
        assert action != Action.SWITCH_CONTROL

        if state.is_standing():
            return cls._roll_when_standing(state, action)

        delta_row, delta_col = cls._COORDS_DELTAS[action]

        rolling_lengthwise = (state.is_lying_horizontally() and delta_col != 0) or (
            state.is_lying_vertically() and delta_row != 0
        )

        if rolling_lengthwise:
            return cls._roll_lengthwise(state, action)
        return cls._roll_sideways(state, action)

    @classmethod
    def _act_when_split(cls, state: State, action: Action) -> State:
        coords1 = state.get_first_coords()
        coords2 = state.get_second_coords()
        controlled_coords = state.get_controlled_cube_coords()
        is_first_cube_controlled = controlled_coords == coords1
        assert controlled_coords is not None

        if action == Action.SWITCH_CONTROL:
            controlled_coords_after_switch = (
                coords2 if is_first_cube_controlled else coords1
            )

            return State(
                coords1,
                coords2,
                state.get_bridges_open_states(),
                state.is_split_status,
                controlled_coords_after_switch,
            )

        else:
            new_controlled_coords = (
                controlled_coords[0] + cls._COORDS_DELTAS[action][0],
                controlled_coords[1] + cls._COORDS_DELTAS[action][1],
            )

            if is_first_cube_controlled:
                return State(
                    new_controlled_coords,
                    coords2,
                    state.get_bridges_open_states(),
                    True,
                    new_controlled_coords,
                )
            else:
                return State(
                    coords1,
                    new_controlled_coords,
                    state.get_bridges_open_states(),
                    True,
                    new_controlled_coords,
                )

    @classmethod
    def _roll_when_standing(cls, state: State, action: Action) -> State:
        assert not state.is_split()

        delta_row, delta_col = cls._COORDS_DELTAS[action]
        row1, col1 = state.coords1
        row2, col2 = state.coords2

        return State(
            (row1 + delta_row, col1 + delta_col),
            (row2 + delta_row * 2, col2 + delta_col * 2),
            state.get_bridges_open_states(),
            False,
            None,
        )

    @classmethod
    def _roll_lengthwise(cls, state: State, action: Action) -> State:
        assert not state.is_split()

        delta_row, delta_col = cls._COORDS_DELTAS[action]
        row1, col1 = state.coords1
        row2, col2 = state.coords2

        rolling_right_or_down = delta_row + delta_col > 0

        if rolling_right_or_down:
            new_row, new_col = (row2 + delta_row, col2 + delta_col)
        else:
            new_row, new_col = row1 + delta_row, col1 + delta_col

        return State(
            (new_row, new_col),
            (new_row, new_col),
            state.get_bridges_open_states(),
            False,
            None,
        )

    @classmethod
    def _roll_sideways(cls, state: State, action: Action) -> State:
        delta_row, delta_col = cls._COORDS_DELTAS[action]
        row1, col1 = state.coords1
        row2, col2 = state.coords2

        return State(
            (row1 + delta_row, col1 + delta_col),
            (row2 + delta_row, col2 + delta_col),
            state.get_bridges_open_states(),
            False,
            None,
        )
