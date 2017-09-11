class Tile:
    """
    A tile of the map and its properties
    """
    # Main types
    T_VOID = '0'
    T_BLOCK = '1'  # Might be the wall of a grotto or of a room, trees or boulders
    T_GROUND = '2'  # Generic - can be grass as well.
    T_LIQUID = '3'  # A specific division of the floor

    # Sub Types
    S_VOID = '0_0'

    # Blocking / High elevation types or deep water. Nobody can pass.
    S_TREE = '1_1'
    S_WALL = '1_2'
    S_BOULDER = '1_3'
    S_DEEP_WATER = '1_4'

    # Floor for regular ground
    S_FLOOR = '2_0'  # Regular dirt
    S_PATH = '2_1'
    S_GRASS = '2_2'
    S_CARPET = '2_3'

    # Liquid - for non blocking ground
    S_WATER = '3_1'  # Only Aquatics will be able to cross
    S_LAVA = '3_2'

    def __init__(self, tile_type=T_VOID, sub_type=S_VOID):
        self.tile_type = tile_type
        self.tile_subtype = sub_type
        self.explored = False

    def block_for(self, entity):
        if self.tile_type in {Tile.T_VOID, Tile.T_BLOCK}:
            return True
        if entity.blocking_tile_list is None:
            # We apply the default list... We base ourselves only on the subtype
            return self.tile_subtype in {Tile.S_WATER}
        return self.tile_subtype in entity.blocking_tile_list