from typing import ClassVar

from game.core.action import Action
from game.core.coordinate import Coordinate
from game.core.level import Level
from game.core.state import State
from game.core.switch import SwitchActionType


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
        bridges_open_default = self.level.get_bridges_open_default_states()

        start_state = State(
            start_coords,
            start_coords,
            bridges_open_default,
        )

        return start_state

    def is_goal(self, state: State) -> bool:
        goal_coords = self.level.get_goal()

        return state.is_standing() and state.get_first_coords() == goal_coords

    def successors(self, state: State) -> list[State]:
        successors = []

        for action in list(Action):
            move_result = self.move_and_check_validity_and_switch_trigger(state, action)

            if move_result is not None:
                successors.append(move_result)

        return successors

    def move_and_check_validity_and_switch_trigger(
        self, state: State, action: Action
    ) -> State | None:
        new_state = self.move_and_check_validity(state, action)

        if new_state is None:
            return new_state

        return self.check_switch_trigger_and_activate_if_true(new_state)

    def check_switch_trigger_and_activate_if_true(self, state: State) -> State:
        BRIDGE_STATE_CHANGE_FROM_SWITCH_ACTION_MAP = {
            SwitchActionType.TOGGLE: lambda x: not x,
            SwitchActionType.PERMANENT_CLOSE: lambda x: False,
            SwitchActionType.PERMANENT_OPEN: lambda x: True,
        }

        triggered_switch_coords = self.get_switch_coords_if_triggered(state)

        if not triggered_switch_coords:
            return state

        new_bridges_open_states = state.get_bridges_open_states()

        for coord in triggered_switch_coords:
            associated_bridges, switch_action_type = (
                self.level.get_bridges_and_action_type_from_switch(coord)
            )

            bridge_state_change_func = BRIDGE_STATE_CHANGE_FROM_SWITCH_ACTION_MAP[
                switch_action_type
            ]

            for bridge in associated_bridges:
                new_bridges_open_states[bridge] = bridge_state_change_func(
                    new_bridges_open_states[bridge]
                )

        return State(
            state.get_first_coords(),
            state.get_second_coords(),
            new_bridges_open_states,
        )

    def get_switch_coords_if_triggered(self, state: State) -> list[Coordinate]:
        coords1 = state.get_first_coords()
        coords2 = state.get_second_coords()

        triggered_switch_coords = []

        standing_on_switch = self.level.is_switch(coords1) and state.is_standing()
        lying_on_soft_switch_with_coords1 = self.level.is_soft_switch(coords1)
        lying_on_soft_switch_with_coords2 = self.level.is_soft_switch(coords2)

        if standing_on_switch or lying_on_soft_switch_with_coords1:
            triggered_switch_coords.append(coords1)
        if lying_on_soft_switch_with_coords2 and coords2 != coords1:
            triggered_switch_coords.append(coords2)

        return triggered_switch_coords

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
            state.get_bridges_open_states(),
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

        return State(
            (new_row, new_col),
            (new_row, new_col),
            state.get_bridges_open_states(),
        )

    def roll_sideways(self, state: State, action: Action) -> State:
        delta_row, delta_col = self.COORDS_DELTAS[action]
        row1, col1 = state.coord1
        row2, col2 = state.coord2

        return State(
            (row1 + delta_row, col1 + delta_col),
            (row2 + delta_row, col2 + delta_col),
            state.get_bridges_open_states(),
        )

    def is_valid_state(self, state: State) -> bool:
        is_valid_coords1 = self.level.is_valid_tile(
            state.get_first_coords(), state.get_bridges_open_states()
        )

        is_valid_coords2 = self.level.is_valid_tile(
            state.get_second_coords(), state.get_bridges_open_states()
        )

        is_standing_on_fragile = state.is_standing() and self.level.is_fragile_tile(
            state.get_first_coords()
        )

        return is_valid_coords1 and is_valid_coords2 and not is_standing_on_fragile
