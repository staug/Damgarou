from entity.gameentity import GameEntity
from shared import GLOBAL
from region.tile import Tile


class Player(GameEntity):

    def __init__(self):
        GameEntity.__init__(self, pos=(1,1), image_ref="PLAYER_PALADIN", z_level=2)
        self.name = "PLAYER"
        self.mule_list = []
        self.fighter_list = []
        self.speed = 10

        self.test_attribute = 100

    def __str__(self):
        return self.name

    def switch_region(self, old_region, new_region):
        self.remove_entity_from_region(old_region)

        GLOBAL.game.current_region = new_region
        if new_region.last_player_position is None:
            (self.x, self.y) = new_region.get_all_available_tiles(Tile.T_GROUND, new_region.region_entities).pop()
        else:
            (self.x, self.y) = new_region.last_player_position
        self.assign_entity_to_region(new_region)

        GLOBAL.game.invalidate_fog_of_war = True

    def move(self, dx=0, dy=0):
        """
        Try to move the player.
        Return True if an action was done (either move or attack)
        """
        self.test_attribute -= 1

        # We keep the old position
        GLOBAL.game.current_region.last_player_position = self.pos

        # Test if we enter the actionable zone of an entity
        for entity in GLOBAL.game.current_region.region_entities:
            if entity != self and entity.actionable is not None and \
                            (self.x + dx, self.y + dy) in entity.actionable.action_field:
                self.x += dx
                self.y += dy
                ok_to_move = entity.actionable.action(self)
                self.x -= dx
                self.y -= dy
                if entity.blocks:
                    if ok_to_move is not None and not ok_to_move:
                        # We triggered an object, and it prevented the move (like a door not opening)
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

            # TODO: variable costs
            # self.game.ticker.ticks_to_advance += self.speed_cost_for(c.AC_ENV_MOVE)
            GLOBAL.game.current_region.ticker.ticks_to_advance += self.speed
            return True

        return False
