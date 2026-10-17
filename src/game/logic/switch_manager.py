from game.core.coordinate import Coordinate
from game.core.level import Level
from game.core.state import State
from game.logic.switch_activator import SwitchActivator


class SwitchManager:
    def __init__(self, level: Level) -> None:
        self.level = level

    def check_and_activate_switches(self, state: State) -> State:
        triggered_switches_coords = self._get_triggered_switches_coords(state)

        new_state = state

        for coords in triggered_switches_coords:
            new_state = self._activate_triggered_switch(coords, new_state)

        return new_state

    def _activate_triggered_switch(
        self, triggered_switch_coords: Coordinate, state: State
    ) -> State:
        coords_and_actions = self.level.get_associated_coords_and_actions_from_switch(
            triggered_switch_coords
        )

        if self.level.is_split_switch(triggered_switch_coords):
            return SwitchActivator.activate_split_switch(
                state, (coords_and_actions[0][0], coords_and_actions[1][0])
            )
        else:
            return SwitchActivator.activate_bridge_switch(state, coords_and_actions)

    def _get_triggered_switches_coords(self, state: State) -> list[Coordinate]:
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
