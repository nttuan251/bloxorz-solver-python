from game.core.coordinate import Coordinate


class State:
    def __init__(self, coord1: Coordinate, coord2: Coordinate) -> None:
        coord1, coord2 = sorted([coord1, coord2])

        self.coord1 = coord1
        self.coord2 = coord2

    def get_first_coords(self) -> Coordinate:
        return self.coord1

    def get_second_coords(self) -> Coordinate:
        return self.coord2

    def is_standing(self) -> bool:
        return self.coord1 == self.coord2

    def is_lying_horizontally(self) -> bool:
        return self.coord1[0] == self.coord2[0]

    def is_lying_vertically(self) -> bool:
        return self.coord1[1] == self.coord2[1]
