class GameState:
    def __init__(self, matrix):
        self.matrix = matrix
        self.rows = len(matrix)
        self.cols = len(matrix[0])
        self.cur_r, self.cur_c = self._find_start_position()
        self.cur_ori = 'STANDING'  # 'STANDING', 'LYING_H', 'LYING_V'

    def _find_start_position(self):
        for r, row in enumerate(self.matrix):
            for c, val in enumerate(row):
                if val == 'S':
                    return r, c
        return 0, 0

    def get_next_state(self, action):
        """Tính toán (r, c, ori) tiếp theo, vị trí Pivot và trục xoay mà không can thiệp render"""
        r, c, ori = self.cur_r, self.cur_c, self.cur_ori

        if ori == 'STANDING':
            mapping = {
                'RIGHT': ((r, c + 1, 'LYING_H'), (c + 0.5, 0, -r), (0, 0, 90)),
                'LEFT':  ((r, c - 2, 'LYING_H'), (c - 0.5, 0, -r), (0, 0, -90)),
                'UP':    ((r - 2, c, 'LYING_V'), (c, 0, -r + 0.5), (90, 0, 0)),
                'DOWN':  ((r + 1, c, 'LYING_V'), (c, 0, -r - 0.5), (-90, 0, 0)),
            }
        elif ori == 'LYING_H':
            mapping = {
                'RIGHT': ((r, c + 2, 'STANDING'), (c + 1.5, 0, -r), (0, 0, 90)),
                'LEFT':  ((r, c - 1, 'STANDING'), (c - 0.5, 0, -r), (0, 0, -90)),
                'UP':    ((r - 1, c, 'LYING_H'), (c + 0.5, 0, -r + 0.5), (90, 0, 0)),
                'DOWN':  ((r + 1, c, 'LYING_H'), (c + 0.5, 0, -r - 0.5), (-90, 0, 0)),
            }
        elif ori == 'LYING_V':
            mapping = {
                'RIGHT': ((r, c + 1, 'LYING_V'), (c + 0.5, 0, -(r + 0.5)), (0, 0, 90)),
                'LEFT':  ((r, c - 1, 'LYING_V'), (c - 0.5, 0, -(r + 0.5)), (0, 0, -90)),
                'UP':    ((r - 1, c, 'STANDING'), (c, 0, -r + 0.5), (90, 0, 0)),
                'DOWN':  ((r + 2, c, 'STANDING'), (c, 0, -(r + 1.5)), (-90, 0, 0)),
            }

        return mapping[action]