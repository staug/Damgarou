from entity.gameentity import GameEntity, ActionableEntity
from entity.livingentities import FighterEntity
from utilities import MName
import random

from shared import GLOBAL

"""
Town and its content
"""


class Town(GameEntity):

    TOWN_INDEX = 1

    def __init__(self, name=None, pos=None, wilderness_index=0):
        GameEntity.__init__(self,
                            pos=pos,
                            image_ref="TOWN",
                            z_level=0,
                            actionable=ActionableEntity(radius=0, actionable_by_player_only=True, function=enter_town))
        self.blocks = True
        if name:
            self.name = name
        else:
            self.name = "Town " + str(Town.TOWN_INDEX)
            Town.TOWN_INDEX = Town.TOWN_INDEX + 1

        self.wilderness_index = wilderness_index


def enter_town(town_entity, entity_that_triggers):
    print("{} enter {}".format(entity_that_triggers, town_entity.name))
    GLOBAL.game.player.switch_region(GLOBAL.game.current_region,
                                     GLOBAL.game.world[town_entity.name])
    return False


"""
Town buildings
"""


class Building(GameEntity):

    def __init__(self):
        self.size = None
        self.top_left_pos = None

    def get_position_inside(self):
        """
        Return a random position inside the building (excluding the wall)
        :return:
        """
        dx = random.randint(1, self.size[0] - 1)
        dy = random.randint(1, self.size[1] - 1)
        return (self.top_left_pos[0] + dx, self.top_left_pos[1] + dy)

    def post_init(self):
        """
        This method is called by the town once the building has been set, positioned and registered
        Can be used to add entities for example, or set additional properties
        :return:
        """
        print("Method not implemented for " + self.name)

    def is_guild_fighter(self):
        return False


class Bank(Building):

    BANK_INDEX = 1

    def __init__(self, name=None, pos=None, town_name=None):
        GameEntity.__init__(self,
                            pos=pos,
                            image_ref="BUILDING_BANK",
                            z_level=0,
                            actionable=ActionableEntity(radius=0, actionable_by_player_only=True,
                                                        function=enter_building))

        if name:
            self.name = name
        else:
            self.name = "Bank " + str(Bank.BANK_INDEX)
            Bank.BANK_INDEX += 1

        self.town_name = town_name


class GuildFighter(Building):
    GF_INDEX = 1

    def __init__(self, name=None, pos=None, town_name=None):
        GameEntity.__init__(self,
                            pos=pos,
                            image_ref="BUILDING_GUILD_FIGHTER",
                            z_level=0,
                            actionable=ActionableEntity(radius=0, actionable_by_player_only=True,
                                                        function=enter_building))

        if name:
            self.name = name
        else:
            self.name = "Guild Fighter " + str(GuildFighter.GF_INDEX)
            GuildFighter.GF_INDEX += 1

        self.town_name = town_name
        self.fighter_list = []

    def post_init(self):
        """
        Add some wandering entities
        Add fighters to the guild of fighter-Warning, fighters are not like living  entities
        :return: None
        """
        for i in range(random.randint(1, 4)):
            fighter = FighterEntity(MName.person_name(), self.get_position_inside())
            fighter.assign_entity_to_region(self.region)
            self.fighter_list.append(fighter)

        # for i in range(random.randint(1, 7)):
        #    self.fighter_list.append(FighterEntity())


    def is_guild_fighter(self):
        return True


def enter_fighter_guild(building_entity, entity_that_triggers):
    GLOBAL.game.screens[GLOBAL.game.GAME_STATE_BUILDING].attach_building(building_entity)
    GLOBAL.game.update_state(GLOBAL.game.GAME_STATE_BUILDING)

    print("{} enter {}".format(entity_that_triggers, building_entity.name))
    return False


class GuildMule(Building):
    GM_INDEX = 1

    def __init__(self, name=None, pos=None, town_name=None):
        GameEntity.__init__(self,
                            pos=pos,
                            image_ref="BUILDING_GUILD_MULE",
                            z_level=0,
                            actionable=ActionableEntity(radius=0, actionable_by_player_only=True,
                                                        function=enter_building))

        if name:
            self.name = name
        else:
            self.name = "Guild Mule " + str(GuildMule.GM_INDEX)
            GuildMule.GM_INDEX += 1

        self.town_name = town_name


class Shop(Building):
    SHOP_INDEX = 1

    def __init__(self, name=None, pos=None, town_name=None):
        GameEntity.__init__(self,
                            pos=pos,
                            image_ref="BUILDING_SHOP",
                            z_level=0,
                            actionable=ActionableEntity(radius=0, actionable_by_player_only=True,
                                                        function=enter_building))

        if name:
            self.name = name
        else:
            self.name = "Shop " + str(Shop.SHOP_INDEX)
            Shop.SHOP_INDEX += 1

        self.town_name = town_name


class Tavern(Building):
    TAVERN_INDEX = 1

    def __init__(self, name=None, pos=None, town_name=None):
        GameEntity.__init__(self,
                            pos=pos,
                            image_ref="BUILDING_TAVERN",
                            z_level=0,
                            actionable=ActionableEntity(radius=0, actionable_by_player_only=True,
                                                        function=enter_building))

        if name:
            self.name = name
        else:
            self.name = "Tavern " + str(Tavern.TAVERN_INDEX)
            Tavern.TAVERN_INDEX += 1

        self.town_name = town_name


class Temple(Building):
    TEMPLE_INDEX = 1

    def __init__(self, name=None, pos=None, town_name=None):
        GameEntity.__init__(self,
                            pos=pos,
                            image_ref="BUILDING_TEMPLE",
                            z_level=0,
                            actionable=ActionableEntity(radius=0, actionable_by_player_only=True,
                                                        function=enter_building))

        if name:
            self.name = name
        else:
            self.name = "Temple " + str(Temple.TEMPLE_INDEX)
            Temple.TEMPLE_INDEX += 1

        self.town_name = town_name


class Townhall(Building):
    TH_INDEX = 1

    def __init__(self, name=None, pos=None, town_name=None):
        GameEntity.__init__(self,
                            pos=pos,
                            image_ref="BUILDING_TOWNHALL",
                            z_level=0,
                            actionable=ActionableEntity(radius=0, actionable_by_player_only=True,
                                                        function=enter_building))

        if name:
            self.name = name
        else:
            self.name = "Townhall " + str(Townhall.TH_INDEX)
            Townhall.TH_INDEX += 1

        self.town_name = town_name


class Trade(Building):
    TRADE_INDEX = 1

    def __init__(self, name=None, pos=None, town_name=None):
        GameEntity.__init__(self,
                            pos=pos,
                            image_ref="BUILDING_TRADE",
                            z_level=0,
                            actionable=ActionableEntity(radius=0, actionable_by_player_only=True,
                                                        function=enter_building))

        if name:
            self.name = name
        else:
            self.name = "Tradepost " + str(Trade.TRADE_INDEX)
            Trade.TRADE_INDEX += 1

        self.town_name = town_name


class Entrance(Building):
    ENTRANCE_INDEX = 1

    def __init__(self, name=None, pos=None, town_name=None):
        GameEntity.__init__(self,
                            pos=pos,
                            image_ref="BUILDING_ENTRANCE",
                            z_level=0,
                            actionable=ActionableEntity(radius=0, actionable_by_player_only=True,
                                                        function=enter_wilderness))

        if name:
            self.name = name
        else:
            self.name = "Entrance " + str(Entrance.ENTRANCE_INDEX)
            Entrance.ENTRANCE_INDEX += 1

        self.blocks = True
        self.town_name = town_name


def enter_wilderness(building_entity, entity_that_triggers):
    print("{} enter {}".format(entity_that_triggers, building_entity.name))
    wilderness_region_name = GLOBAL.game.world[building_entity.town_name].town.wilderness_index
    GLOBAL.game.player.switch_region(GLOBAL.game.current_region,
                                     GLOBAL.game.world[wilderness_region_name])
    return False


def enter_building(building_entity, entity_that_triggers):
    GLOBAL.game.screens[GLOBAL.game.GAME_STATE_BUILDING].attach_building(building_entity)
    GLOBAL.game.update_state(GLOBAL.game.GAME_STATE_BUILDING)

    print("{} enter {}".format(entity_that_triggers, building_entity.name))
    return False
