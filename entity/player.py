from entity.gameentity import GameEntity
from shared import GLOBAL
from region.tile import Tile


class Player(GameEntity):

    def __init__(self):
        GameEntity.__init__(self, pos=(1, 1), image_ref="PLAYER_PALADIN", z_level=2, blocks=True)

        self.mule_list = []
        self.fighter_list = []
        self.inventory = []
        self.equipment = []

        self.speed = 10

        self.name = "PLAYER"

        self.race = None

        self.charisma = None  # cost of sales, ability to bribe enemy
        self.friendship = None  # more or less friends, impact the loyalty of the group
        self.erudition = None  # detect usage of object
        self.strength = None  # capable of carrying more objects

        self.money = 0
        self.food_level = 0

    @property
    def protection(self):
        return None

    @property
    def attack(self):
        return None

    """
        * name
* race:
- help sell/buy from certain person
- prevent the buy from certain products (note that for mule, that means that they will refuse to carry the products)
- prevent the equipment of certain objects
* previous occupation: gives bonus on equipment? Allow to craft?
* charisma: gives bonus/malus to costs of sales, ability to bribe enemies
* friendship: gives more/less friends, impact the loyalty of the people in the group. A low
* objects: gives more/less objects slots
* food consumption [impacted by strength, inverse].
* exposure to elements: there are 4 elements (fire/earth/water/ether). Any person is always either immune to 2 and double penalized to 2, equally attached to 4 (no bonus/malus) or immune to 1, pealized by one and equal to 2.
* strength: gives more/less capacities to transport. More strength means more food is consumed!
* erudition level: able to detect usage of objects, getting more gold (unidentified object will have 1/10th of the value). More erudition means more arrogant, so charisma going down!
 [to buy/sell merchandise]
money level
inventory slots
[to survive]
health
protection
attack (this doesn?t exist for player, this is low by default as he is supposed to be a merchant!)
food level
[attached to the player]
object slots
friends slots
curse/benediction: player may be cursed/blessed (limited time, impact one/several attributes)

        """

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
