from entity.gameentity import GameEntity
from shared import GLOBAL


class Player(GameEntity):

    def __init__(self):
        GameEntity.__init__(self, pos=(1,1), image_ref="PLAYER_PALADIN", z_level=2)

        self.mule_list = []
        self.fighter_list = []

    def move(self, dx=0, dy=0):
        """
        Try to move the player.
        Return True if an action was done (either move or attack)
        """
        # We keep the old position
        GLOBAL.game.current_region.last_player_position = self.pos

        # Test if we enter the actionable zone of an entity
        for entity in GLOBAL.game.current_region.region_entities:
            if entity != self and entity.actionable is not None and \
                            (self.x + dx, self.y + dy) in entity.actionable.action_field:
                self.x += dx
                self.y += dy
                result = entity.actionable.action(self)
                self.x -= dx
                self.y -= dy
                if result is not None and not result:
                    # We triggered an object, it prevented the move (like a door not opening)
                    return False

        # Test if we collide with an other enemy, then we enter in a fight mode

        # Test if we collide with the terrain, and terrain only
        destination_tile = GLOBAL.game.current_region.tiles[self.x + dx][self.y + dy]
        if not destination_tile.block_for(self):
            # now test the list of objects
            for entity in GLOBAL.game.current_region.region_entities:
                if entity != self and entity.blocks and entity.x == self.x + dx and entity.y == self.y + dy:
                    return False
            # success
            self.x += dx
            self.y += dy
            if self.animated and (dx != 0 or dy != 0):
                self.last_direction = (dx, dy)

            GLOBAL.game.invalidate_fog_of_war = True
            #self.game.ticker.ticks_to_advance += self.speed_cost_for(c.AC_ENV_MOVE)
            return True

        return False
