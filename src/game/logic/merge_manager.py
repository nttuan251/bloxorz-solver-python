from src.game.core.state import State


class MergeManager:
    @classmethod
    def check_and_activate_merge(cls, state: State) -> State:
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
