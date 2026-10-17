from game.core.action import Action
from game.core.level import Level
from game.core.state import State
from game.logic.merge_manager import MergeManager
from game.logic.state_mover import StateMover
from game.logic.switch_manager import SwitchManager


class StateManager:
    def __init__(self, level: Level) -> None:
        self.level = level
        self.switch_manager = SwitchManager(level)
        self.merge_manager = MergeManager()

    def act_and_activate_triggers(self, state: State, action: Action) -> State | None:
        new_state = self._act_and_validate(state, action)

        if new_state is None:
            return new_state

        if not state.is_split():
            # Note that after the cube is splitted, even if the mini cubes are next to each other, they don't merge.
            return self._check_and_activate_switches_and_validate(new_state)

        elif action != Action.SWITCH_CONTROL:
            new_state_after_merge = self.merge_manager.check_and_activate_merge(
                new_state
            )

            # Note that switches are checked after merging, that way the switches that could be triggered by the other mini cube are also activated.
            return self._check_and_activate_switches_and_validate(new_state_after_merge)

        else:
            # Note that switching does NOT trigger switches or merges
            return new_state

    def _check_and_activate_switches_and_validate(self, state: State) -> State | None:
        new_state = self.switch_manager.check_and_activate_switches(state)

        if self._is_valid_state(new_state):
            return new_state

        return None

    def _act_and_validate(self, state: State, action: Action) -> State | None:
        new_state = StateMover.act(state, action)

        if self._is_valid_state(new_state):
            return new_state

        return None

    def _is_valid_state(self, state: State) -> bool:
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
