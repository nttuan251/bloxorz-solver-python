from src.game.core.coordinate import Coordinate
from src.game.core.state import State


class MoveInfoDeterminer:
    @staticmethod
    def is_switch_control(current_state: State, next_state: State) -> bool:
        return (
            current_state.is_split()
            and next_state.is_split()
            and current_state.get_first_coords() == next_state.get_first_coords()
            and current_state.get_second_coords() == next_state.get_second_coords()
            and current_state.get_controlled_cube_coords()
            != next_state.get_controlled_cube_coords()
        )

    @staticmethod
    def is_mini_cube_move(current_state: State, next_state: State) -> bool:
        return current_state.is_split() and not MoveInfoDeterminer.is_switch_control(
            current_state, next_state
        )

    @staticmethod
    def get_newly_landed_on_tiles(
        current_state: State, next_state: State
    ) -> set[Coordinate]:
        newly_landed_on_tiles = {
            next_state.get_first_coords(),
            next_state.get_second_coords(),
        }

        if not current_state.is_split():
            return newly_landed_on_tiles

        current_landed_on_tiles = {
            current_state.get_first_coords(),
            current_state.get_second_coords(),
        }

        return newly_landed_on_tiles - current_landed_on_tiles

    @staticmethod
    def activated_switch(current_state: State, next_state: State) -> bool:
        bridge_switch_activated = (
            current_state.get_bridges_open_states()
            != next_state.get_bridges_open_states()
        )
        split_switch_activated = not current_state.is_split() and next_state.is_split()

        return bridge_switch_activated or split_switch_activated

    @staticmethod
    def is_stand_up(current_state: State, next_state: State) -> bool:
        return (
            not current_state.is_split()
            and not current_state.is_standing()
            and not next_state.is_split()
            and next_state.is_standing()
        )
