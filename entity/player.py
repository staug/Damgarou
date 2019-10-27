import random

from entity.gameentity import GameEntity
from region.tile import Tile
from shared import GLOBAL


class Player(GameEntity):

    def __init__(self, player_dict=None):
        assert player_dict is not None, "No data as part of the player dict"

        image_ref = random.choice(
            ("PLAYER_ENGINEER", "PLAYER_MAGE", "PLAYER_PALADIN", "PLAYER_ROGUE", "PLAYER_WARRIOR"))

        GameEntity.__init__(self, pos=(1, 1), image_ref=image_ref, z_level=2, blocks=True)

        self.mule_list = []
        self.fighter_list = []
        self.inventory = []
        self.equipment = []

        self.speed = 10

        self.name = player_dict["Name"]
        self.gender = player_dict["Gender"]

        self.race = player_dict["Race"]

        self.charisma = player_dict["Charisma"]  # cost of sales, ability to bribe enemy
        self.friendship = player_dict["Friendship"]  # more or less friends, impact the loyalty of the group
        self.erudition = player_dict["Erudition"]  # detect usage of object
        self.strength = player_dict["Strength"]  # capable of carrying more objects

        self.money = random.randint(10, 200)
        self.food_level = 0

        self.age = 20
        self.married_with = None
        self.child = None

    @property
    def protection(self):
        prot = 0
        for fighter in self.fighter_list:
            prot += fighter.protection
        return prot

    @property
    def attack(self):
        att = 0
        for fighter in self.fighter_list:
            att += fighter.attack
        return att

    @property
    def max_allies(self):
        return int(self.friendship / 10) + 2

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

    def add_fighter(self, fighter):
        """
        Try to add the fighter to the list. Return False if not possible due to max allies, gold...
        # TODO: test if gold is enough
        :param fighter: the fighter to add
        :return: True in case of success, False otherwise
        """
        if len(self.fighter_list) < self.max_allies:
            self.fighter_list.append(fighter)
            fighter.remove_entity_from_region(fighter.region)
            return True
        return False
