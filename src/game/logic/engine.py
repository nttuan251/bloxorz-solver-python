from src.game.core.action import Action
from src.game.core.level import Level
from src.game.core.move import Move
from src.game.core.state import State
from src.game.logic.state_manager import StateManager


class BloxorzGame:
    def __init__(self, level: Level) -> None:
        self.level = level
        self.state_manager = StateManager(level)

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

    def successors(self, state: State) -> list[Move]:
        successors: list[Move] = []

        for action in list(Action):
            if action == Action.SWITCH_CONTROL and not state.is_split():
                continue

            move_result = self.state_manager.act_and_activate_triggers(state, action)

            if move_result is not None:
                successors.append((action, move_result))

        return successors
