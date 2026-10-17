from game.core.coordinate import Coordinate
from game.core.state import State
from game.core.switch import SwitchActionType


class SwitchActivator:
    @classmethod
    def activate_split_switch(
        cls,
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

    @classmethod
    def activate_bridge_switch(
        cls,
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
