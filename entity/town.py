from entity.gameentity import GameEntity, ActionableEntity
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

        if name:
            self.name = name
        else:
            self.name = "Town " + str(Town.TOWN_INDEX)
            Town.TOWN_INDEX = Town.TOWN_INDEX + 1

        self.wilderness_index = wilderness_index

def enter_town(town_entity, entity_that_triggers):
    print("{} enter {}".format(entity_that_triggers, town_entity.name))
    return False

"""
Town buildings
"""


class Bank(GameEntity):

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


class GuildFighter(GameEntity):
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


class GuildMule(GameEntity):
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


class Shop(GameEntity):
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


class Tavern(GameEntity):
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


class Temple(GameEntity):
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


class Townhall(GameEntity):
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


class Trade(GameEntity):
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


class Entrance(GameEntity):
    ENTRANCE_INDEX = 1

    def __init__(self, name=None, pos=None, town_name=None):
        GameEntity.__init__(self,
                            pos=pos,
                            image_ref="BUILDING_ENTRANCE",
                            z_level=0,
                            actionable=ActionableEntity(radius=0, actionable_by_player_only=True,
                                                        function=enter_building))

        if name:
            self.name = name
        else:
            self.name = "Entrance " + str(Entrance.ENTRANCE_INDEX)
            Entrance.ENTRANCE_INDEX += 1

        self.town_name = town_name


def enter_building(building_entity, entity_that_triggers):
    GLOBAL.game.screens[GLOBAL.game.GAME_STATE_BUILDING].attach_building(building_entity)
    GLOBAL.game.game_state = GLOBAL.game.GAME_STATE_BUILDING

    print("{} enter {}".format(entity_that_triggers, building_entity.name))
    return False