from src.game.core.coordinate import Coordinate


class State:
    def __init__(
        self,
        coords1: Coordinate,
        coords2: Coordinate,
        bridges_open_states: dict[Coordinate, bool],
        is_split_status: bool,
        controlled_cube_coords: Coordinate | None,
    ) -> None:
        assert (is_split_status and controlled_cube_coords is not None) or (
            not is_split_status and controlled_cube_coords is None
        )

        if controlled_cube_coords is not None:
            assert controlled_cube_coords in (coords1, coords2)

        coords1, coords2 = sorted([coords1, coords2])

        self.coords1 = coords1
        self.coords2 = coords2
        self.bridges_open_states = bridges_open_states.copy()
        self.is_split_status = is_split_status
        self.controlled_cube_coords = controlled_cube_coords

        self._key = (
            self.coords1,
            self.coords2,
            frozenset(self.bridges_open_states.items()),
            self.is_split_status,
            self.controlled_cube_coords,
        )
        self._hash = hash(self._key)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, State):
            raise TypeError(
                "Cannot compare object of State type with object of other types."
            )
        return self._hash == other._hash and self._key == other._key

    def __hash__(self) -> int:
        return self._hash

    def get_first_coords(self) -> Coordinate:
        return self.coords1

    def get_second_coords(self) -> Coordinate:
        return self.coords2

    def get_bridges_open_states(self) -> dict[Coordinate, bool]:
        return self.bridges_open_states.copy()

    def get_controlled_cube_coords(self) -> Coordinate | None:
        return self.controlled_cube_coords

    def is_standing(self) -> bool:
        return self.coords1 == self.coords2

    def is_lying_horizontally(self) -> bool:
        return (
            not self.is_split_status
            and not self.is_standing()
            and self.coords1[0] == self.coords2[0]
        )

    def is_lying_vertically(self) -> bool:
        return (
            not self.is_split_status
            and not self.is_standing()
            and self.coords1[1] == self.coords2[1]
        )

    def is_split(self) -> bool:
        return self.is_split_status
