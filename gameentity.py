"""
Generic Game entity, which may be displayed on the map (town, player, trap, object...)
Most of the object base code will go there
"""


class GameEntity:

    def __init__(self, pos=None):
        self.pos = pos

    @property
    def x(self):
        if not self.pos:
            return -1
        return self.pos[0]

    @property
    def y(self):
        if not self.pos:
            return -1
        return self.pos[1]
