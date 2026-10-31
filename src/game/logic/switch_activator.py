from collections.abc import Callable
from typing import ClassVar

from src.game.core.coordinate import Coordinate
from src.game.core.state import State
from src.game.core.switch import SwitchActionType


class SwitchActivator:
    BRIDGE_STATE_CHANGE_FROM_SWITCH_ACTION_MAP: ClassVar[
        dict[SwitchActionType, Callable[[bool], bool]]
    ] = {
        SwitchActionType.TOGGLE: lambda x: not x,
        SwitchActionType.PERMANENT_CLOSE: lambda x: False,
        SwitchActionType.PERMANENT_OPEN: lambda x: True,
    }

    @classmethod
    def activate_split_switch(
        cls,
        state: State,
        associated_split_coords: tuple[Coordinate, Coordinate],
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
        bridges_and_actions: list[tuple[Coordinate, SwitchActionType]],
    ) -> State:
        new_bridges_open_states = state.get_bridges_open_states()

        for bridge, action in bridges_and_actions:
            bridge_state_change_func = cls.BRIDGE_STATE_CHANGE_FROM_SWITCH_ACTION_MAP[
                action
            ]

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
