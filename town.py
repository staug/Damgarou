from gameentity import GameEntity

"""
Town and its content
"""


class Town(GameEntity):

    TOWN_INDEX = 1

    def __init__(self, name=None, pos=None):
        GameEntity.__init__(self, pos=pos)  # dimensions doivent être impair!

        if name:
            self.name = name
        else:
            self.name = "Town " + str(Town.TOWN_INDEX)
            Town.TOWN_INDEX = Town.TOWN_INDEX + 1