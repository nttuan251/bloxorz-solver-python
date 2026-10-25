from typing import ClassVar

from src.game.core.state import State
from src.solver_algorithms.cost.cost_calculator import CostCalculator
from src.solver_algorithms.cost.move_info_determiner import MoveInfoDeterminer


class SwitchFriendlyCostCalculator(CostCalculator):
    """The example from the assignment: fragile tiles are expensive, switches are cheap.

    - ROLL_COST for a normal roll or a mini cube move,
    - SWITCH_COST for a move that presses a switch (opens / closes a bridge or
      teleports the block): switches move the puzzle forward,
    - FRAGILE_COST for landing on a fragile tile (risky); it wins over SWITCH_COST
      when one move does both,
    - SWITCH_CONTROL_COST for switching the controlled cube while split.
    Every cost is >= 1, which the admissible heuristics rely on.
    """

    ROLL_COST: ClassVar[float] = 1.1
    SWITCH_COST: ClassVar[float] = 1
    FRAGILE_COST: ClassVar[float] = 3
    SWITCH_CONTROL_COST: ClassVar[float] = 1.5

    def calculate_cost(self, current_state: State, next_state: State) -> float:
        if MoveInfoDeterminer.is_switch_control(current_state, next_state):
            return self.SWITCH_CONTROL_COST

        newly_landed_on_tiles = MoveInfoDeterminer.get_newly_landed_on_tiles(
            current_state, next_state
        )

        if any(self.level.is_fragile_tile(coords) for coords in newly_landed_on_tiles):
            return self.FRAGILE_COST

        if MoveInfoDeterminer.activated_switch(current_state, next_state):
            return self.SWITCH_COST

        return self.ROLL_COST
