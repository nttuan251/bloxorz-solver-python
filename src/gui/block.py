from ursina import Entity, Vec3, color, curve, destroy, invoke, scene
import config

class Block:
    def __init__(self, start_r, start_c):
        self.entity = Entity(model='cube', color=color.orange)
        self.is_animating = False
        self.set_transform(start_r, start_c, 'STANDING')

    def get_transform(self, r, c, ori):
        if ori == 'STANDING':
            return Vec3(c, 1.0, -r), Vec3(0.9, 2.0, 0.9)
        elif ori == 'LYING_H':
            return Vec3(c + 0.5, 0.5, -r), Vec3(1.9, 0.9, 0.9)
        elif ori == 'LYING_V':
            return Vec3(c, 0.5, -(r + 0.5)), Vec3(0.9, 0.9, 1.9)

    def set_transform(self, r, c, ori):
        pos, scale = self.get_transform(r, c, ori)
        self.entity.position = pos
        self.entity.scale = scale
        self.entity.rotation = Vec3(0, 0, 0)

    def animate_roll(self, pivot_pos, rot_axis, next_r, next_c, next_ori):
        self.is_animating = True
        pivot = Entity(position=Vec3(*pivot_pos))
        self.entity.world_parent = pivot

        pivot.animate_rotation(Vec3(*rot_axis), duration=config.ROLL_DURATION, curve=curve.linear)

        def finish():
            self.entity.world_parent = scene
            destroy(pivot)
            self.set_transform(next_r, next_c, next_ori)
            self.is_animating = False

        invoke(finish, delay=config.ROLL_DURATION)