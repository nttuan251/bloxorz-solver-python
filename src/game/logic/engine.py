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
            start_coords, start_coords, bridges_open_default, False, None
        )

        return start_state

    def is_goal(self, state: State) -> bool:
        goal_coords = self.level.get_goal()

        return state.is_standing() and state.get_first_coords() == goal_coords

    def successors(self, state: State) -> list[State]:
        successors = []

        for action in list(Action):
            if action == Action.SWITCH_CONTROL and not state.is_split():
                continue

            move_result = self.act_and_activate_triggers(state, action)

            if move_result is not None:
                successors.append(move_result)

        return successors

    def act_and_activate_triggers(self, state: State, action: Action) -> State | None:
        new_state = self.act_and_check_validity(state, action)

        if new_state is None:
            return new_state

        if not state.is_split():
            # Note that after the cube is splitted, even if the mini cubes are next to each other, they don't merge.
            return self.check_switch_trigger_and_activate_and_validate_if_true(
                new_state
            )

        elif action != Action.SWITCH_CONTROL:
            new_state_after_merge_check = self.check_merge_trigger_and_activate_if_true(
                new_state
            )

            # Note that switches are checked after merging, that way the switches that could be triggered by the other mini cube are also activated.
            return self.check_switch_trigger_and_activate_and_validate_if_true(
                new_state_after_merge_check
            )

        else:
            # Note that switching does NOT trigger switches or merges
            return new_state

    def check_merge_trigger_and_activate_if_true(self, state: State) -> State:
        assert state.is_split()

        row1, col1 = state.get_first_coords()
        row2, col2 = state.get_second_coords()

        horizontally_adjacent = row1 == row2 and abs(col1 - col2) == 1
        vertically_adjacent = col1 == col2 and abs(row1 - row2) == 1

        if horizontally_adjacent or vertically_adjacent:
            return State(
                state.get_first_coords(),
                state.get_second_coords(),
                state.get_bridges_open_states(),
                False,
                None,
            )
        return state

    def check_switch_trigger_and_activate_and_validate_if_true(
        self, state: State
    ) -> State | None:
        triggered_switch_coords = self.get_switch_coords_if_triggered(state)

        new_state = state

        for coords in triggered_switch_coords:
            new_state = self.activate_triggered_switch(coords, new_state)

        if self.is_valid_state(new_state):
            return new_state
        return None

    def activate_triggered_switch(
        self, triggered_switch_coords: Coordinate, state: State
    ) -> State:
        associated_coords, switch_action_type = (
            self.level.get_associated_coords_and_action_type_from_switch(
                triggered_switch_coords
            )
        )

        if switch_action_type == SwitchActionType.SPLIT:
            return self.activate_split_switch(state, associated_coords)
        else:
            return self.activate_bridge_switch(
                state, associated_coords, switch_action_type
            )

    def activate_split_switch(
        self,
        state: State,
        associated_split_coords: list[Coordinate],
    ) -> State:
        return State(
            associated_split_coords[0],
            associated_split_coords[1],
            state.get_bridges_open_states(),
            True,
            associated_split_coords[0],
        )

    def activate_bridge_switch(
        self,
        state: State,
        associated_bridges: list[Coordinate],
        switch_action_type: SwitchActionType,
    ) -> State:
        new_bridges_open_states = state.get_bridges_open_states()

        BRIDGE_STATE_CHANGE_FROM_SWITCH_ACTION_MAP = {
            SwitchActionType.TOGGLE: lambda x: not x,
            SwitchActionType.PERMANENT_CLOSE: lambda x: False,
            SwitchActionType.PERMANENT_OPEN: lambda x: True,
        }

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
            state.is_split(),
            state.get_controlled_cube_coords(),
        )

    def get_switch_coords_if_triggered(self, state: State) -> list[Coordinate]:
        coords1 = state.get_first_coords()
        coords2 = state.get_second_coords()

        is_first_cube_controlled = state.get_controlled_cube_coords() == coords1

        triggered_switch_coords = []

        standing_on_switch = self.level.is_switch(coords1) and state.is_standing()
        triggering_soft_switch_with_coords1 = self.level.is_soft_switch(coords1) and (
            not state.is_split() or (state.is_split() and is_first_cube_controlled)
        )
        triggering_soft_switch_with_coords2 = self.level.is_soft_switch(coords2) and (
            not state.is_split() or (state.is_split() and not is_first_cube_controlled)
        )

        if standing_on_switch or triggering_soft_switch_with_coords1:
            triggered_switch_coords.append(coords1)
        if triggering_soft_switch_with_coords2 and coords2 != coords1:
            triggered_switch_coords.append(coords2)

        return triggered_switch_coords

    def act_and_check_validity(self, state: State, action: Action) -> State | None:
        new_state = self.act(state, action)

        if self.is_valid_state(new_state):
            return new_state

        return None

    def act(self, state: State, action: Action) -> State:
        if state.is_split():
            return self.act_when_split(state, action)
        else:
            return self.act_when_whole(state, action)

    def act_when_whole(self, state: State, action: Action) -> State:
        assert action != Action.SWITCH_CONTROL

        if state.is_standing():
            return self.roll_when_standing(state, action)

        delta_row, delta_col = self.COORDS_DELTAS[action]

        rolling_lengthwise = (state.is_lying_horizontally() and delta_col != 0) or (
            state.is_lying_vertically() and delta_row != 0
        )

        if rolling_lengthwise:
            return self.roll_lengthwise(state, action)
        return self.roll_sideways(state, action)

    def act_when_split(self, state: State, action: Action) -> State:
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
                controlled_coords[0] + self.COORDS_DELTAS[action][0],
                controlled_coords[1] + self.COORDS_DELTAS[action][1],
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

    def roll_when_standing(self, state: State, action: Action) -> State:
        assert not state.is_split()

        delta_row, delta_col = self.COORDS_DELTAS[action]
        row1, col1 = state.coords1
        row2, col2 = state.coords2

        return State(
            (row1 + delta_row, col1 + delta_col),
            (row2 + delta_row * 2, col2 + delta_col * 2),
            state.get_bridges_open_states(),
            False,
            None,
        )

    def roll_lengthwise(self, state: State, action: Action) -> State:
        assert not state.is_split()

        delta_row, delta_col = self.COORDS_DELTAS[action]
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

    def roll_sideways(self, state: State, action: Action) -> State:
        delta_row, delta_col = self.COORDS_DELTAS[action]
        row1, col1 = state.coords1
        row2, col2 = state.coords2

        return State(
            (row1 + delta_row, col1 + delta_col),
            (row2 + delta_row, col2 + delta_col),
            state.get_bridges_open_states(),
            False,
            None,
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

        is_split_and_overlapping = (
            state.is_split() and state.get_first_coords() == state.get_second_coords()
        )

        return (
            is_valid_coords1
            and is_valid_coords2
            and not is_standing_on_fragile
            and not is_split_and_overlapping
        )
