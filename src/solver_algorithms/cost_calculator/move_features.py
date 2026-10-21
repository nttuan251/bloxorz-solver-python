from src.game.core.coordinate import Coordinate
from src.game.core.state import State


class MoveFeatures:
    """What kind of move turned current_state into next_state (used by cost calculators)."""

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
    def is_cube_move(current_state: State, next_state: State) -> bool:
        """A mini cube moved while the block was split (merging moves included)."""
        return current_state.is_split() and not MoveFeatures.is_switch_control(
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
    def activates_switch(current_state: State, next_state: State) -> bool:
        """The move changed a bridge or teleported the block through a split switch."""
        bridges_changed = (
            current_state.get_bridges_open_states()
            != next_state.get_bridges_open_states()
        )
        teleported = not current_state.is_split() and next_state.is_split()

        return bridges_changed or teleported

    @staticmethod
    def stands_block_up(current_state: State, next_state: State) -> bool:
        """A lying 1x1x2 block was rolled up onto one cell."""
        return (
            not current_state.is_split()
            and not current_state.is_standing()
            and not next_state.is_split()
            and next_state.is_standing()
        )
