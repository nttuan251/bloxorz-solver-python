from core.Action import Action

state_type = tuple[tuple[int, int], tuple[int, int], float]

move_type = tuple[state_type, Action, float]
