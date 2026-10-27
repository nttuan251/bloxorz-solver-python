from typing import ClassVar

from src.game.core.state import State
from src.solver_algorithms.cost.cost_calculator import CostCalculator
from src.solver_algorithms.cost.move_info_determiner import MoveInfoDeterminer


class SwitchFriendlyCostCalculator(CostCalculator):
    ROLL_COST: ClassVar[float] = 1.1
    SWITCH_COST: ClassVar[float] = 1
    FRAGILE_COST: ClassVar[float] = 3
    SWITCH_CONTROL_COST: ClassVar[float] = 0  # switching cubes is not a step (project FAQ #23)

    def calculate_cost(self, current_state: State, next_state: State) -> float:
        if MoveInfoDeterminer.is_switch_control(current_state, next_state):
            return self.SWITCH_CONTROL_COST

        newly_landed_on_tiles = MoveInfoDeterminer.get_newly_landed_on_tiles(
            current_state, next_state
        )

        # A 1x1x1 mini cube never breaks a fragile tile (project FAQ #16), so only the
        # whole block is charged for landing on one.
        if not next_state.is_split() and any(
            self.level.is_fragile_tile(coords) for coords in newly_landed_on_tiles
        ):
            return self.FRAGILE_COST

        if MoveInfoDeterminer.activated_switch(current_state, next_state):
            return self.SWITCH_COST

        return self.ROLL_COST
