import random
from os import path

import pygame as pg

from default import *
from region.tile import Tile
from entity.town import Town
from entity.door import Door
from entity.livingentities import FriendlyEntity
from entity.building_deco import MuralLamp
from shared import GLOBAL
from utilities import AStar, SQ_Location, SQ_MapHandler, Ticker


class RegionFactory:
    """
    Used to generate one of the predefined map type.
    Each region is saved according to its name. If the name already exists, simply returns the region.
    """

    REGION_WILDERNESS = "WILDERNESS"
    REGION_DUNGEON = "DUNGEON"
    REGION_TOWN = "TOWN"

    REGION_DICT = {}

    @staticmethod
    def invoke(name,
               state=None,
               region_type=REGION_WILDERNESS,
               dimension=(81, 121),
               **attributes):
        """
        :param name: The name of the region. Can be used as a future reference
        :param state: All maps are generated using random things. This is to define the seed of the region.
        :param region_type: The type of the region. This can be (so far) a wilderness, a dungeon or a town.
        :param dimension: The dimension of the region
        """
        assert name is not None, "All regions must have a name"

        if name in RegionFactory.REGION_DICT:
            return RegionFactory.REGION_DICT[name]

        if state is not None:
            random.setstate(state)

        region_correctly_initialized = False
        region = None

        while not region_correctly_initialized:
            if region_type == RegionFactory.REGION_WILDERNESS:
                assert "town_list" in attributes, "Wilderness region needs to have a town list"
                region = WildernessRegion(name, dimension, town_list=attributes["town_list"], with_liquid=True)
                region_correctly_initialized = region.is_valid_map()
                if region_correctly_initialized:
                    # Now we register the entities on the "region"
                    for town_region in attributes["town_list"]:
                        town_region.town.assign_entity_to_region(region)
                    # We add some friendly guys
                    all_positions = region.get_all_available_tiles(without_objects=True, tile_type=Tile.T_GROUND)
                    for i in range(20):
                        FriendlyEntity("Friendly {}".format(i), all_positions.pop()).assign_entity_to_region(region)

            elif region_type == RegionFactory.REGION_TOWN:
                assert "building_list" in attributes, "Town region needs to have a building list"
                region = TownRegion(name, dimension, building_entity_list=attributes["building_list"])
                region.town = Town(name=name)
                # We register the building in the town
                if attributes["wilderness_index"]:
                    region.town.wilderness_index = attributes["wilderness_index"]

                for building in attributes["building_list"]:
                    building.town_name = region.name
                    building.assign_entity_to_region(region)

                for door_characteristics in region.door_list:
                    door = Door((door_characteristics[1], door_characteristics[2]),
                                    door_characteristics[0])
                    door.assign_entity_to_region(region)

                # Let's add some decoration inside...
                # TODO move that to the post init?
                for building in attributes["building_list"]:
                    if building.size != (3, 3):
                        for north_wall_index in range(building.top_left_pos[0] + 1,
                                                  building.top_left_pos[0] + building.size[0] - 1):
                            position = (north_wall_index, building.top_left_pos[1])
                            if region.position_without_entity(position):
                                chance = random.randint(0, 100)
                                if 0 <= chance < 50:
                                    lamp = MuralLamp((north_wall_index, building.top_left_pos[1]), "1")
                                    lamp.assign_entity_to_region(region)
                                elif 50 <= chance < 100:
                                    lamp = MuralLamp((north_wall_index, building.top_left_pos[1]), "2")
                                    lamp.assign_entity_to_region(region)

                # Let's call the post init method that are specific to the buildings
                for building in attributes["building_list"]:
                    building.post_init()

                region_correctly_initialized = True  # A town is always correct!
        RegionFactory.REGION_DICT["name"] = region

        return region


class Region:
    """
    The Region, representing a combination of tiles and entities that belong in this space.
    Mainly holds a reference to a set of tiles, as well as dimensions as well as a list of entities it uses.
    The list of entities is kept in the sprite groups and in a set
    """

    def __init__(self, name, dimension):

        self.name = name
        self._background = None

        self.tile_width = dimension[0]  # width of map, expressed in tiles
        self.tile_height = dimension[1]  # height of map, expressed in tiles

        self.tiles = []

        # We have 5 sprites groups: two below the player, the player one and two above
        # The player one is the 2.
        # They are drawn in the order 0 to 4
        self.region_entities = set()  # the list of entities of this map
        self.all_groups = []
        for i in range(5):
            self.all_groups.append(pg.sprite.Group())

        self.last_player_position = None

        # Each region has its own ticker for its entities, so that we do not waste time advancing things that are not
        # present on the screen
        self._local_ticker = None

    @property
    def ticker(self):
        if self._local_ticker is None:
            self._local_ticker = Ticker()
        return self._local_ticker

    def _build_background(self, name=None):
        """
        Build the image from the map.
        :param name: Optional filename to store the resulting file
        :return: Nothing
        """
        if self._background is None:
            self._background = pg.Surface((self.tile_width * TILESIZE_SCREEN[0],
                                           self.tile_height * TILESIZE_SCREEN[1]))
            self._background.fill(BGCOLOR)
            self._create_background()

        if name is not None:
            pg.image.save(self._background, path.dirname(__file__) + '/' + name)

    @property
    def background(self):
        if self._background is None:
            self._build_background()
        return self._background

    def _create_background(self):
        assert True, "Method create background was called on region instead of sub class"

    def clean_before_save(self):
        self._background = None

    def remove_extra_blocks(self, replace_with_type=None, replace_with_subtype=None):
        """
        Generic method used by all to clean up after generation
        """
        listing = []

        for x in range(0, self.tile_width):
            for y in range(0, self.tile_height):
                if self.tiles[x][y].tile_type == Tile.T_BLOCK:
                    delta = [(0, -1), (0, 1), (1, 0), (-1, 0), (1, 1), (-1, -1), (1, -1), (-1, 1)]
                    count = 0
                    for (dx, dy) in delta:
                        if x + dx < 0 or x + dx >= self.tile_width or y + dy < 0 or y + dy >= self.tile_height:
                            count += 1
                        elif self.tiles[x + dx][y + dy].tile_type in (Tile.T_BLOCK, Tile.T_VOID):
                            count += 1
                    if count == 8:
                        if not replace_with_type:
                            self.tiles[x][y].tile_type = Tile.T_VOID
                        else:
                            listing.append((x, y))

        if replace_with_type:
            for pos in listing:
                self.tiles[pos[0]][pos[1]].tile_type = replace_with_type
                self.tiles[pos[0]][pos[1]].tile_subtype = replace_with_subtype

    def tile_weight(self, x, y, tiles, tile_type=[Tile.T_BLOCK], tile_subtype=None):
        """
        Taken from http://www.angryfishstudios.com/2011/04/adventures-in-bitmasking/
        :param x:
        :param y:
        :param tiles: the complete tileset
        :param tile_type: the tile type used as reference to count the weight
        :param tile_subtype: the tile subtype to be used (optional)
        :return:
        """
        weight = 0

        if y == 0 or (y - 1 >= 0 and tiles[x][y - 1].tile_type in tile_type and
                          (tile_subtype is None or tiles[x][y - 1].tile_subtype in tile_subtype)):
            weight += 1
        if x == 0 or (x - 1 >= 0 and tiles[x - 1][y].tile_type in tile_type and
                          (tile_subtype is None or tiles[x - 1][y].tile_subtype in tile_subtype)):
            weight += 8
        if (y + 1 < self.tile_height and tiles[x][y + 1].tile_type in tile_type and
                (tile_subtype is None or tiles[x][y + 1].tile_subtype in tile_subtype)) or \
                        y == self.tile_height - 1:
            weight += 4
        if (x + 1 < self.tile_width and tiles[x + 1][y].tile_type in tile_type and
                (tile_subtype is None or tiles[x + 1][y].tile_subtype in tile_subtype)) or \
                        x == self.tile_width - 1:
            weight += 2

        # Correction on the side...
        if x == 0:
            if weight in (11, 13, 14, 15):
                weight -= 8
        elif x == self.tile_width - 1:
            if weight in (7, 11, 14, 15):
                weight -= 2
        elif y == self.tile_height - 1:
            if weight in (7, 13, 14, 15):
                weight -= 4

        return weight

    def get_random_available_tile(self, tile_type, without_objects=True):
        """
        Return a tile matching the characteristics: given tile type
        Used to get a spawning position...
        By default, the tile should be without objects and out of any doors position
        :param tile_type: the type of tile that we look for
        :param without_objects: check if no objects is there, and that it is not a possible door position
        :return: a tile position (tuple)
        """
        entity_pos_listing = set()

        if without_objects:
            for entity in self.region_entities:
                entity_pos_listing.add((entity.x, entity.y))

        while True:
            x = random.randint(0, self.tile_width - 1)
            y = random.randint(0, self.tile_height - 1)
            if self.tiles[x][y].tile_type == tile_type:
                if without_objects and ((x, y) not in entity_pos_listing):
                    return x, y
                elif not without_objects:
                    return x, y

    def get_close_available_tile(self, ref_pos, tile_type, without_objects=True):
        """
        Return a tile matching the characteristics: given tile type near entity
        By default, the tile should be without objects and out of any doors position
        :param ref_pos: the ref position for the object
        :param tile_type: the type of tile that we look for
        :param without_objects: check if no objects is there, and that it is not a possible door position
        :return: a tile position (tuple) that matches free, the ref pos if none is found
        """
        entity_pos_listing = set()

        if without_objects:
            for entity in self.region_entities:
                entity_pos_listing.add((entity.x, entity.y))

        delta = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]
        random.shuffle(delta)
        pos_x, pos_y = ref_pos

        for d in delta:
            x = pos_x + d[0]
            y = pos_y + d[1]
            if self.tiles[x][y].tile_type == tile_type:
                if without_objects and ((x, y) not in entity_pos_listing):
                    return x, y
        return ref_pos

    def get_all_available_tiles(self, tile_type, without_objects=False, shuffle=True):
        """
        Return all tile matching the characteristics: given tile type
        Used to get a spawning position...
        :param tile_type: the type of tile that we look for
        :param without_objects: set to True to remove objects overlap
        :param shuffle: if set to True, shuffle before returning the data
        :return: a list of tile positions (tuple)
        """
        listing = []
        entity_pos_listing = set()

        if without_objects:
            for entity in self.region_entities:
                entity_pos_listing.add((entity.x, entity.y))

        for x in range(self.tile_width):
            for y in range(self.tile_height):
                if self.tiles[x][y].tile_type in tile_type:
                    if without_objects:
                        if (x, y) not in entity_pos_listing:
                            listing.append((x, y))
                    else:
                        listing.append((x, y))
        if shuffle:
            random.shuffle(listing)
        return listing

    def get_all_available_isolated_tiles(self, tile_type, without_objects=False, surrounded=7, max=None, shuffle=True):
        """
        Return all tile matching the characteristics: given tile type, surrounded by 8 cells of same type
        Used to get a spawning position...
        :param tile_type: the types of tile that we look for
        :param without_objects: set to True to remove objects overlap
        :param surrounded: the number of tiles of same type that the tile should have around
        :return: a list of tile positions (tuple)
        """
        listing = set(self.get_all_available_tiles(tile_type, without_objects=without_objects, shuffle=False))
        result = []
        for pos in listing:
            x, y = pos
            v = 0
            for delta in [(-1, -1), (-1, 0), (-1, 1), (0, 1), (0, -1), (1, -1), (1, 0), (1, 1)]:
                dx, dy = delta
                if without_objects and (x + dx, y + dy) in listing:
                    v += 1
                elif 0 <= x + dx < self.tile_width and 0 <= y + dy < self.tile_height:
                    if self.tiles[x + dx][y + dy].tile_type == tile_type:
                        v += 1
                        if v >= surrounded:
                            break
            if v >= surrounded:
                result.append(pos)
                if max and len(result) >= max:
                    return result
        if shuffle:
            random.shuffle(result)
        return result

    def check_all_tile_connected(self, starting_type_type=Tile.T_GROUND):
        """
        Flood the map, starting at one randomly.
        Make sure that all tile of same type are connected.
        :return: true if ok
        """
        tiles_flooded = set()
        tiles_to_flood = set()

        # First, we find a random tile:
        starting_pos = None
        while starting_pos is None:
            x = random.randint(0, self.tile_width - 1)
            y = random.randint(0, self.tile_height - 1)
            if self.tiles[x][y].tile_type == starting_type_type:
                starting_pos = (x, y)

        tiles_to_flood.add(starting_pos)

        # Now we flood in brutal manner
        while len(tiles_to_flood) > 0:
            (current_position_x, current_position_y) = tiles_to_flood.pop()
            tiles_flooded.add((current_position_x, current_position_y))
            # Let's go in all direction
            for (delta_x, delta_y) in ((-1,-1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1,-1), (1,0), (1,1)):
                if 0 <= current_position_x + delta_x < self.tile_width and \
                                        0 <= current_position_y + delta_y < self.tile_height:
                    if self.tiles[current_position_x + delta_x][current_position_y + delta_y].tile_type == \
                            starting_type_type:
                        pos_to_add = (current_position_x + delta_x, current_position_y + delta_y)
                        if pos_to_add not in tiles_to_flood and pos_to_add not in tiles_flooded:
                            tiles_to_flood.add(pos_to_add)


        # Last part: we check the length...
        nb_of_tiles_to_be_flooded = 0
        for y in range(self.tile_height):
            for x in range(self.tile_width):
                if self.tiles[x][y].tile_type == starting_type_type:
                    nb_of_tiles_to_be_flooded += 1
        return nb_of_tiles_to_be_flooded == len(tiles_flooded)

    def position_without_entity(self, position):
        for entity in self.region_entities:
            if entity.pos == position:
                return False
        return True


class WildernessRegion(Region):
    """
    A map which is based on a cellular automaton
    This map can be used for:
    - Surface Town: ground can be dirt or grass. Borders are made of trees. Very smooth, at least 6 repetition to get
    large surface of ground.
    - Subterran Town: Borders are made of hills. Not a lot of smoothing, so the algo is stopped very
    quickly (in the repeat). If there is liquid (Pit) it is lava style.
    - Forest type: ground is lighter, with dirt or grass. Borders are made of trees. Not a lot of smoothing. Liquid is
    made of Water (pit)
    """

    def __init__(self,
                 name,
                 dimension,
                 blocking_type=Tile.S_TREE,
                 with_liquid=False,
                 town_list=None,
                 grotto_list=None):

        assert dimension[0] % 2 == 1 and dimension[1] % 2 == 1, "Maze dimensions must be odd"
        Region.__init__(self, name, dimension)  # dimensions doivent être impair!

        self.tiles = [[Tile(Tile.T_GROUND, sub_type=Tile.S_FLOOR)
                       for _y in range(self.tile_height)]
                      for _x in range(self.tile_width)]

        # Base Ground
        reftiles = WildernessRegion.generate_algo(self.tile_width, self.tile_height, 40,
                                                  ((3, 5, 1), (2, 5, -1)), empty_center=False)
        # Now add some extra stuff depending on the type of map
        # Grass on the floor - to implement we construct a totally new map. We will apply the previous as a mask.
        grass_tile = WildernessRegion.generate_algo(self.tile_width, self.tile_height, 50, ((3, 5, 1), (1, 6, -1)))

        # Some shallow Aquatics
        water_tile = []
        if with_liquid:
            water_tile = WildernessRegion.generate_algo(self.tile_width, self.tile_height, 40, ((2, 5, -1),))

        for y in range(self.tile_height):
            for x in range(self.tile_width):
                if reftiles[x][y] == 1:
                    self.tiles[x][y].tile_type = Tile.T_BLOCK
                    self.tiles[x][y].tile_subtype = blocking_type
                elif with_liquid and water_tile[x][y] == 1:
                    self.tiles[x][y].tile_type = Tile.T_LIQUID
                    self.tiles[x][y].tile_subtype = Tile.S_WATER
                elif grass_tile[x][y] == 1:
                    self.tiles[x][y].tile_subtype = Tile.S_GRASS

        list_available_tiles = self.get_all_available_tiles(Tile.T_GROUND, without_objects=True)
        for town_region in town_list:
            (town_region.town.x, town_region.town.y) = list_available_tiles.pop()

        # And we add some path on the floor to connect the towns
        for index_origin, town_origin in enumerate(town_list[:]):
            for index_destination, town_destination in enumerate(town_list[:]):
                if index_destination > index_origin:
                    # Road from town_origin.name, town_destination.name
                    astar = AStar(SQ_MapHandler(self.tiles, dimension[0], dimension[1]))
                    p = astar.findPath(SQ_Location(town_origin.town.x, town_origin.town.y),
                                       SQ_Location(town_destination.town.x, town_destination.town.y))

                    if p:
                        for n in p.nodes:
                            self.tiles[n.location.x][n.location.y].tile_subtype = Tile.S_PATH

    @staticmethod
    def generate_algo(width, height, initial_noise, repeat_parameters, empty_center=False):
        """
        Create a map, with 1 and 0. See algo at
        http://www.roguebasin.com/index.php?title=Cellular_Automata_Method_for_Generating_Random_Cave-Like_Levels
        :param width: width of the map
        :param height: height of the map
        :param initial_noise: initial "wall" probability (40 for 40%)
        :param repeat_parameters: list of wall generation, it is a list of triple containing
        - first parameter, how many time do we repeat over the procedure (3 means 3 iteration)
        - second parameter, minimum number of wall around the tile to keep the tile as wall (5 means 5 tiles around)
        - third parameter, if there are less than this number of walls around, we make a wall (-1 to skip)
        the third parameter make sit more likely to have "island" in the center
        :param empty_center: remove any wall at the center
        :return:a [][] containing 1 (wall) or 0 (floor)
        """

        tiles = [[0 for y in range(height)] for x in range(width)]

        # Initial Random Noise
        for y in range(height):
            for x in range(width):
                if x in [0, width - 1] or y in [0, height - 1] or random.randint(0, 100) <= initial_noise:
                    tiles[x][y] = 1

        # And do the rounding
        for (number_repeat, number_to_keep, number_to_be_born) in repeat_parameters:
            for repeat in range(number_repeat):
                for y in range(1, height - 1):
                    for x in range(1, width - 1):
                        count = WildernessRegion._count_border_tile(tiles, x, y, 1)
                        if count >= number_to_keep:
                            tiles[x][y] = 1
                        elif number_to_be_born >= 0 and count <= number_to_be_born:
                            tiles[x][y] = 1
                        else:
                            tiles[x][y] = 0

        if empty_center:
            WildernessRegion._eliminate_center_border(tiles, width, height)  # A bit brutal
            for y in range(1, height - 1):  # We smooth a bit the result
                for x in range(1, width - 1):
                    count = WildernessRegion._count_border_tile(tiles, x, y, 1)
                    if count >= number_to_keep:
                        tiles[x][y] = 1
                    else:
                        tiles[x][y] = 0

        return tiles

    @staticmethod
    def _count_border_tile(tiles, posx, posy, comparison_value):
        count = 0
        for x in {posx - 1, posx, posx + 1}:
            for y in {posy - 1, posy, posy + 1}:
                if tiles[x][y] == comparison_value:
                    count += 1
        return count

    @staticmethod
    def _eliminate_center_border(tiles, width, height, value_to_keep=1, value_to_fill=0):
        """
        Assuming a tiles[][] structure, eliminate any value in the "center" which is not the value to keep
        :param tiles:
        :param value_to_keep: the value that won't be erased - typically the walls
        :return: nothing, but changes the tiles
        """
        half_width_min = int(width / 2)
        half_width_max = int(width / 2) + 1

        for y in range(int(height / 6), int(height - height / 6)):
            x_left = 1
            x_right = width - 1
            for x in range(2, half_width_max):
                if tiles[x][y] != value_to_keep:
                    x_left = x - 1
                    break
            for x in range(width - 2, half_width_min, -1):
                if tiles[x][y] != value_to_keep:
                    x_right = x + 1
                    break
            for x in range(x_left, x_right):
                tiles[x][y] = value_to_fill

    def _create_background(self):
        """
        Build background using dawnlike tileset - Redefined here
        :return: Nothing, just blitting things on _background property
        """

        if not hasattr(self, "save_initial_seed"):
            self.save_initial_seed = random.choice((1, 4, 7, 10))

        initial_seed = self.save_initial_seed
        grass_serie = initial_seed + 0
        rock_serie = initial_seed + 1
        dirt_serie = initial_seed + 11
        path_serie = initial_seed + 12
        water_serie = initial_seed + 13

        for y in range(self.tile_height):
            for x in range(self.tile_width):

                if self.tiles[x][y].tile_type == Tile.T_VOID:
                    pass
                else:
                    weight = self.tile_weight(x, y, self.tiles,
                                              tile_type=self.tiles[x][y].tile_type,
                                              tile_subtype=self.tiles[x][y].tile_subtype)

                    if self.tiles[x][y].tile_type == Tile.T_BLOCK:
                        self._background.blit(GLOBAL.img('FLOOR')[rock_serie][weight],
                                              (x * TILESIZE_SCREEN[0], y * TILESIZE_SCREEN[1]))
                    elif self.tiles[x][y].tile_type == Tile.T_GROUND:
                        if self.tiles[x][y].tile_subtype == Tile.S_FLOOR:
                            self._background.blit(GLOBAL.img('FLOOR')[dirt_serie][weight],
                                                  (x * TILESIZE_SCREEN[0], y * TILESIZE_SCREEN[1]))
                        elif self.tiles[x][y].tile_subtype == Tile.S_GRASS:
                            self._background.blit(GLOBAL.img('FLOOR')[grass_serie][weight],
                                                  (x * TILESIZE_SCREEN[0], y * TILESIZE_SCREEN[1]))
                        elif self.tiles[x][y].tile_subtype == Tile.S_PATH:
                            self._background.blit(GLOBAL.img('FLOOR')[path_serie][weight],
                                                  (x * TILESIZE_SCREEN[0], y * TILESIZE_SCREEN[1]))
                    elif self.tiles[x][y].tile_type == Tile.T_LIQUID:
                        if self.tiles[x][y].tile_subtype == Tile.S_WATER:
                            self._background.blit(GLOBAL.img('FLOOR')[water_serie][weight],
                                                  (x * TILESIZE_SCREEN[0], y * TILESIZE_SCREEN[1]))
                    else:
                        print("Unknown type {} subtype {}".format(self.tiles[x][y].tile_type,
                                                                  self.tiles[x][y].tile_subtype))

    def is_valid_map(self):
        return self.check_all_tile_connected()


class TownRegion(Region):
    """
    A town is set of buildings (closed spaces), linked by path.
    """

    class _Building:
        """
        A building is a closed space, dedicated to a set of activities.
        """
        def __init__(self, size, name=None, position=None, one_connection=False):
            """
            Initialize the room
            :param size: the size of the room (tuple)
            :param position: The upper left corner of the room (tuple)
            """
            self.name = name
            self.size = size
            self.position = position
            self.doors = []  # Triplet H/V, x, y (H for horizontal, V for vertical)
            self.connecting_buildings = []
            self.one_connection = one_connection

        def get_center_pos(self):
            pos_x = self.position[0] + int(self.size[0] / 2)
            pos_y = self.position[1] + int(self.size[1] / 2)
            return pos_x, pos_y

    def __init__(self, name, dimension, building_entity_list):

        assert dimension[0] % 2 == 1 and dimension[1] % 2 == 1, "Maze dimensions must be odd"
        assert len(building_entity_list) < int(dimension[0] * dimension[1] / 81 * .9), "Too many buildings for the town"

        building_size_range = ((6, 6), (9, 9))
        assert dimension[0] > building_size_range[1][0] and dimension[1] > building_size_range[1][1],\
            "Dimensions too small for even one building"

        Region.__init__(self, name, dimension)

        # Initialize map
        self.tiles = [[Tile(Tile.T_VOID, sub_type=Tile.S_VOID)
                       for y in range(self.tile_height)]
                      for x in range(self.tile_width)]

        # generate the town
        self.town = None
        self.door_list = []

        # first building - the first building is always the entrance :-)
        current_building = building_entity_list[0]

        _internal_buildings_list = {building_entity_list[0]: self._generate_building((3, 3),
                                                                            (3, 3),
                                                                            name=current_building.name,
                                                                            one_connection=True)}

        self._place_building(_internal_buildings_list[building_entity_list[0]],
                             (int(self.tile_width / 2 - (_internal_buildings_list[building_entity_list[0]].size[0] / 2)),
                              int(self.tile_height / 2 - (_internal_buildings_list[building_entity_list[0]].size[1] / 2))))

        # all the others
        while len(_internal_buildings_list) != len(building_entity_list):
            current_building = building_entity_list[len(_internal_buildings_list)]
            branching_building = _internal_buildings_list[random.choice(list(_internal_buildings_list.keys()))]  # This gives less a chain
            while branching_building.one_connection and len(branching_building.connecting_buildings) > 0:
                # We want to ensure that some building like the Entrance are only linked to one
                branching_building = _internal_buildings_list[
                    random.choice(list(_internal_buildings_list.keys()))]

            choice_wall = self._get_branching_position_direction(branching_building)
            branching_pos = (choice_wall[0], choice_wall[1])
            branching_dir = choice_wall[2]
            new_building = self._generate_building(building_size_range[0], building_size_range[1], name=current_building.name)
            path_length = random.randint(3, 7)
            door_type = 'H'
            if branching_dir == 'N':
                door_type = 'V'
                new_building_pos = (int(branching_pos[0] - (new_building.size[0] / 2)),
                                    int(branching_pos[1] - new_building.size[1] + 1 - path_length))
            elif branching_dir == 'E':
                new_building_pos = (int(branching_pos[0] + path_length),
                                    int(branching_pos[1] - (new_building.size[1] / 2)))
            elif branching_dir == 'S':
                door_type = 'V'
                new_building_pos = (int(branching_pos[0] - (new_building.size[0] / 2)),
                                    int(branching_pos[1] + path_length))
            elif branching_dir == 'W':
                new_building_pos = (int(branching_pos[0] - (new_building.size[0]) + 1 - path_length),
                                    int(branching_pos[1] - (new_building.size[1] / 2)))

            if self._space_for_new_building(new_building.size, new_building_pos):
                self._place_building(new_building, new_building_pos)
                building_entity_list[len(_internal_buildings_list)].x,\
                building_entity_list[len(_internal_buildings_list)].y = new_building.get_center_pos()  # this is the game entity
                _internal_buildings_list[building_entity_list[len(_internal_buildings_list)]] = new_building

                # Now connecting room
                # No tunnel, easy case:
                if branching_building.size != (3, 3):
                    branching_building.doors.append((door_type, branching_pos[0], branching_pos[1]))
                self._make_floor(branching_pos[0], branching_pos[1])
                new_building.connecting_buildings.append(branching_building)
                branching_building.connecting_buildings.append(new_building)
                # We now place the tunnel
                if branching_dir == 'N':
                    for i in range(1, path_length + 1):
                        self._make_floor(branching_pos[0], branching_pos[1] - i)
                        # self._make_wall(branching_pos[0] - 1, branching_pos[1] - i)
                        # self._make_wall(branching_pos[0] + 1, branching_pos[1] - i)
                    if path_length >= 3 and new_building.size != (3, 3):
                        new_building.doors.append(('V', branching_pos[0], branching_pos[1] - path_length))
                elif branching_dir == 'E':
                    for i in range(1, path_length + 1):
                        self._make_floor(branching_pos[0] + i, branching_pos[1])
                        # self._make_wall(branching_pos[0] + i, branching_pos[1] - 1)
                        # self._make_wall(branching_pos[0] + i, branching_pos[1] + 1)
                    if path_length >= 3 and new_building.size != (3, 3):
                        new_building.doors.append(('H', branching_pos[0] + path_length, branching_pos[1]))
                elif branching_dir == 'S':
                    for i in range(1, path_length + 1):
                        self._make_floor(branching_pos[0], branching_pos[1] + i)
                        # self._make_wall(branching_pos[0] - 1, branching_pos[1] + i)
                        # self._make_wall(branching_pos[0] + 1, branching_pos[1] + i)
                        if path_length >= 3 and new_building.size != (3, 3):
                            new_building.doors.append(('V', branching_pos[0], branching_pos[1] + path_length))
                elif branching_dir == 'W':
                    for i in range(1, path_length + 1):
                        self._make_floor(branching_pos[0] - i, branching_pos[1])
                        # self._make_wall(branching_pos[0] - i, branching_pos[1] - 1)
                        # self._make_wall(branching_pos[0] - i, branching_pos[1] + 1)
                    if path_length >= 3 and new_building.size != (3, 3):
                        new_building.doors.append(('H', branching_pos[0] - path_length, branching_pos[1]))

        # Any building that is 3x3 (Entrance...) we remove the walls - and the doors (even if should not be)
        for building in _internal_buildings_list:
            if _internal_buildings_list[building].size == (3, 3):
                self._place_building(_internal_buildings_list[building],
                                     _internal_buildings_list[building].position,
                                     force_floor=True)
                _internal_buildings_list[building].doors = []

        # Now we crop the town
        # The town is ar too big for the number of buildings. We only leave a small square around the building.
        border = 3
        # remove extreme right part
        index_x = self.tile_width - 1
        found = False
        while not found:
            for index_y in range(self.tile_height):
                if self.tiles[index_x][index_y].tile_type != Tile.T_VOID:
                    found = True
            index_x -= 1
        remove_extreme_right = max(self.tile_width - index_x - 2 - border, 0)
        # remove left part:
        index_x = 0
        found = False
        while not found:
            for index_y in range(self.tile_height):
                if self.tiles[index_x][index_y].tile_type != Tile.T_VOID:
                    found = True
            index_x += 1
        remove_extreme_left = max(index_x - 1 - border, 0)
        # remove bottom part
        index_y = self.tile_height - 1
        found = False
        while not found:
            for index_x in range(self.tile_width):
                if self.tiles[index_x][index_y].tile_type != Tile.T_VOID:
                    found = True
            index_y -= 1
        remove_extreme_bottom = max(self.tile_height - index_y - 2 - border, 0)
        # remove upper part
        index_y = 0
        found = False
        while not found:
            for index_x in range(self.tile_width):
                if self.tiles[index_x][index_y].tile_type != Tile.T_VOID:
                    found = True
            index_y += 1
        remove_extreme_top = max(index_y - 1 - border, 0)

        # let's adjust accordingly the position of the building entities, the only one which matters
        self.tile_height -= remove_extreme_bottom + remove_extreme_top
        self.tile_width -= remove_extreme_left + remove_extreme_right

        handled_door_pos = []
        for building_entity in _internal_buildings_list.keys():
            old_pos_x, old_pos_y = _internal_buildings_list[building_entity].get_center_pos()
            building_entity.x = old_pos_x - remove_extreme_left
            building_entity.y = old_pos_y - remove_extreme_top
            old_left_x, old_top_y = _internal_buildings_list[building_entity].position
            building_entity.top_left_pos = (old_left_x - remove_extreme_left,
                                        old_top_y - remove_extreme_top)
            building_entity.size = _internal_buildings_list[building_entity].size
            # let's adjust the doors
            doorlist = []
            for door in _internal_buildings_list[building_entity].doors:
                x, y = door[1] - remove_extreme_left, door[2] - remove_extreme_top
                doorlist.append((door[0], x, y))
                if (x, y) not in handled_door_pos:
                    handled_door_pos.append((x, y))
                    self.door_list.append((door[0], x, y))
            _internal_buildings_list[building_entity].doors = doorlist

        # Now all buildings are placed, let's add some decoration.
        walls_building = self.tiles[:]  # We copy the current tiles
        self.tiles = [[Tile(Tile.T_GROUND, sub_type=Tile.S_FLOOR)
                       for y in range(self.tile_height)]
                      for x in range(self.tile_width)]

        reftiles = WildernessRegion.generate_algo(self.tile_width, self.tile_height, 40,
                                                  ((3, 5, 1), (2, 5, -1)), empty_center=False)
        # Grass on the floor - to implement we construct a totally new map. We will apply the previous as a mask.
        grass_tile = WildernessRegion.generate_algo(self.tile_width, self.tile_height, 50, ((3, 5, 1), (1, 6, -1)))

        # Some shallow Aquatics
        water_tile = WildernessRegion.generate_algo(self.tile_width, self.tile_height, 40, ((2, 5, -1),))

        for y in range(self.tile_height):
            for x in range(self.tile_width):
                if walls_building[x + remove_extreme_left][y + remove_extreme_top].tile_type != Tile.T_VOID:
                    self.tiles[x][y].tile_type = walls_building[x + remove_extreme_left][y + remove_extreme_top].tile_type
                    self.tiles[x][y].tile_subtype = walls_building[x + remove_extreme_left][y + remove_extreme_top].tile_subtype
                else:
                    if reftiles[x][y] == 1:
                        self.tiles[x][y].tile_type = Tile.T_BLOCK
                        self.tiles[x][y].tile_subtype = Tile.S_BOULDER
                    elif water_tile[x][y] == 1:
                        self.tiles[x][y].tile_type = Tile.T_LIQUID
                        self.tiles[x][y].tile_subtype = Tile.S_WATER
                    elif grass_tile[x][y] == 1:
                        self.tiles[x][y].tile_subtype = Tile.S_GRASS

        # Setup the player starting position near the entrance to wilderness
        self.last_player_position = building_entity_list[0].pos


    def _generate_building(self, min_size, max_size, modulo_rest=2, name=None, one_connection=False):
        """
        Generate a building according to the criteria
        :param min_size: tuple with the minimum dimension
        :param max_size: tuple with the max dimension
        :param modulo_rest: put to 0 for even dimensions, 1 for odd, 2 if do not care (default)
        :return:
        """
        size_x = random.randint(min_size[0], max_size[0])
        size_y = random.randint(min_size[1], max_size[1])
        if modulo_rest < 2:
            while size_x % 2 != modulo_rest:
                size_x = random.randint(min_size[0], max_size[0])
            while size_y % 2 != modulo_rest:
                size_y = random.randint(min_size[1], max_size[1])
        return TownRegion._Building((size_x, size_y), name=name, one_connection=one_connection)

    def _place_building(self, building, grid_position, force_floor=False):
        building.position = grid_position
        for y in range(grid_position[1], grid_position[1] + building.size[1]):
            for x in range(grid_position[0], grid_position[0] + building.size[0]):
                if force_floor:
                    self._make_floor(x, y)
                else:
                    if y in (grid_position[1], grid_position[1] + building.size[1] - 1) or \
                                    x in (grid_position[0], grid_position[0] + building.size[0] - 1):
                        self._make_wall(x, y)
                    else:
                        self._make_floor(x, y)

    def _get_branching_position_direction(self, branching_building, except_dir=None):
        while True:
            # we consider pos = 0,0
            walls = {'N': [(x, 0) for x in range(1, branching_building.size[0] - 1)],
                     'S': [(x, branching_building.size[1] - 1) for x in range(1, branching_building.size[0] - 1)],
                     'W': [(0, y) for y in range(1, branching_building.size[1] - 1)],
                     'E': [(branching_building.size[0] - 1, y) for y in range(1, branching_building.size[1] - 1)]}
            valid_list = ['N', 'S', 'E', 'W']
            if except_dir is not None:
                for direction in except_dir:
                    if direction is not None:
                        valid_list.remove(direction)
            direction = random.choice(valid_list)
            target = random.choice(walls[direction])
            # We don't want doors next to doors...
            x = target[0] + branching_building.position[0]
            y = target[1] + branching_building.position[1]
            if direction in ('N', 'S'):
                if not (self.tiles[x - 1][y].tile_type == Tile.T_GROUND or
                                self.tiles[x + 1][y].tile_type == Tile.T_GROUND):
                    return x, y, direction
            if direction in ('E', 'W'):
                if not (self.tiles[x][y-1].tile_type == Tile.T_GROUND or self.tiles[x][y+1].tile_type == Tile.T_GROUND):
                    return x, y, direction

    def _space_for_new_building(self, new_building_size, new_building_position, tiles_blocking=Tile.T_GROUND, border=1):
        for y in range(new_building_position[1] - border,
                       new_building_position[1] + new_building_size[1] + border):
            for x in range(new_building_position[0] - border,
                           new_building_position[0] + new_building_size[0] + border):
                if x < 0 or x > self.tile_width - 1:
                    return False
                if y < 0 or y > self.tile_height - 1:
                    return False
                if self.tiles[x][y].tile_type in tiles_blocking:
                    return False
        return True

    def _make_wall(self, x, y):
        self.tiles[x][y].tile_type = Tile.T_BLOCK
        self.tiles[x][y].tile_subtype = Tile.S_WALL

    def _make_floor(self, x, y):
        self.tiles[x][y].tile_type = Tile.T_GROUND
        self.tiles[x][y].tile_subtype = Tile.S_CARPET

    def _create_background(self):
        """
        Build background using dawnlike tileset - Redefined here
        :return: Nothing, just blitting things on _background property
        """
        if not hasattr(self, "save_carpet"):
            self.save_carpet = random.choice((13, 16, 19, 22))
        carpet_serie = self.save_carpet

        wall_serie = 1

        if not hasattr(self, "save_initial_seed"):
            self.save_initial_seed = random.choice((1, 4, 7, 10))

        initial_seed = self.save_initial_seed
        grass_serie = initial_seed + 0
        rock_serie = initial_seed + 1
        dirt_serie = initial_seed + 11
        path_serie = initial_seed + 12
        water_serie = initial_seed + 13

        for y in range(self.tile_height):
            for x in range(self.tile_width):
                if self.tiles[x][y].tile_type == Tile.T_VOID:
                    pass
                else:
                    weight = self.tile_weight(x, y, self.tiles,
                                              tile_type=self.tiles[x][y].tile_type,
                                              tile_subtype=self.tiles[x][y].tile_subtype)

                    tile_type = self.tiles[x][y].tile_type
                    tile_subtype = self.tiles[x][y].tile_subtype

                    if tile_type == Tile.T_BLOCK:
                        if tile_subtype == Tile.S_BOULDER:
                            self._background.blit(GLOBAL.img('FLOOR')[rock_serie][weight],
                                                  (x * TILESIZE_SCREEN[0], y * TILESIZE_SCREEN[1]))
                        elif tile_subtype == Tile.S_WALL:
                            self._background.blit(GLOBAL.img('WALLS')[wall_serie][weight],
                                                  (x * TILESIZE_SCREEN[0], y * TILESIZE_SCREEN[1]))

                    elif self.tiles[x][y].tile_type == Tile.T_GROUND:
                        if self.tiles[x][y].tile_subtype == Tile.S_FLOOR:
                            self._background.blit(GLOBAL.img('FLOOR')[dirt_serie][weight],
                                                  (x * TILESIZE_SCREEN[0], y * TILESIZE_SCREEN[1]))
                        elif self.tiles[x][y].tile_subtype == Tile.S_GRASS:
                            self._background.blit(GLOBAL.img('FLOOR')[grass_serie][weight],
                                                  (x * TILESIZE_SCREEN[0], y * TILESIZE_SCREEN[1]))
                        elif self.tiles[x][y].tile_subtype == Tile.S_PATH:
                            self._background.blit(GLOBAL.img('FLOOR')[path_serie][weight],
                                                  (x * TILESIZE_SCREEN[0], y * TILESIZE_SCREEN[1]))
                        elif self.tiles[x][y].tile_subtype == Tile.S_CARPET:
                            self._background.blit(GLOBAL.img('FLOOR')[carpet_serie][weight],
                                                  (x * TILESIZE_SCREEN[0], y * TILESIZE_SCREEN[1]))
                    elif self.tiles[x][y].tile_type == Tile.T_LIQUID:
                        if self.tiles[x][y].tile_subtype == Tile.S_WATER:
                            self._background.blit(GLOBAL.img('FLOOR')[water_serie][weight],
                                                  (x * TILESIZE_SCREEN[0], y * TILESIZE_SCREEN[1]))
                    else:
                        print("Unknown type {} subtype {}".format(self.tiles[x][y].tile_type,
                                                                  self.tiles[x][y].tile_subtype))
