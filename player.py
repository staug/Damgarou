from gameentity import GameEntity


class Player(GameEntity):

    def __init__(self):
        GameEntity.__init__(self, pos=(1,1), image_ref="PLAYER_PALADIN", z_level=2)

    def move(self, dx=0, dy=0):
        self.x += dx
        self.y += dy
        if self.animated and (dx != 0 or dy != 0):
            self.last_direction = (dx, dy)