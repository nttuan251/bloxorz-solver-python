from ursina import Entity, Vec3
import config

class Board:
    def __init__(self, matrix):
        self.tiles = {}
        self._build_board(matrix)

    def _build_board(self, matrix):
        for r, row in enumerate(matrix):
            for c, val in enumerate(row):
                if val != '-':
                    tile_color = config.TILE_COLORS.get(val, config.TILE_COLORS['o'])
                    t = Entity(
                        model='cube',
                        color=tile_color,
                        position=Vec3(c, 0, -r),
                        scale=config.TILE_SCALE
                    )
                    self.tiles[(r, c)] = t