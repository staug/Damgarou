from entity.gameentity import GameEntity, ActionableEntity

"""
Town and its content
"""


class Town(GameEntity):

    TOWN_INDEX = 1

    def __init__(self, name=None, pos=None):
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


def enter_town(town_entity, entity_that_triggers):
    print("{} enter {}".format(entity_that_triggers, town_entity.name))