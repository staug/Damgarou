import random
from os import path

import pygame as pg

from default import *
from region.tile import Tile
from shared import GLOBAL
from utilities import AStar, SQ_Location, SQ_MapHandler


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
                    for town in attributes["town_list"]:
                        region.region_entities.add(town)
                        town.assign_entity_to_region(region)
                print("MAP CORRECT: " + str(region_correctly_initialized))

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

    def tile_weight(self, x, y, tiles, tile_type=(Tile.T_BLOCK), tile_subtype=None):
        """
        Taken from http://www.angryfishstudios.com/2011/04/adventures-in-bitmasking/
        :param x:
        :param y:
        :param tiles: the complete tileset
        :param tile_type: the tyle type used as reference to count the weight
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

    def get_random_available_tile(self, tile_type, region_objects, without_objects=True):
        """
        Return a tile matching the characteristics: given tile type
        Used to get a spawning position...
        By default, the tile should be without objects and out of any doors position
        :param tile_type: the type of tile that we look for
        :param without_objects: check if no objects is there, and that it is not a possible door position
        :param region_objects: the list of current objects in the game
        :return: a tile position (tuple)
        """
        entity_pos_listing = set()

        if without_objects:
            for entity in region_objects:
                entity_pos_listing.add((entity.x, entity.y))

        while True:
            x = random.randint(0, self.tile_width - 1)
            y = random.randint(0, self.tile_height - 1)
            if self.tiles[x][y].tile_type == tile_type:
                if without_objects and ((x, y) not in entity_pos_listing):
                    return x, y
                elif not without_objects:
                    return x, y

    def get_close_available_tile(self, ref_pos, tile_type, region_objects, without_objects=True):
        """
        Return a tile matching the characteristics: given tile type near entity
        By default, the tile should be without objects and out of any doors position
        :param ref_pos: the ref position for the object
        :param tile_type: the type of tile that we look for
        :param without_objects: check if no objects is there, and that it is not a possible door position
        :param region_objects: the list of current objects in the game
        :return: a tile position (tuple) that matches free, the ref pos if none is found
        """
        entity_pos_listing = set()

        if without_objects:
            for entity in region_objects:
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

    def get_all_available_tiles(self, tile_type, region_objects, without_objects=False, shuffle=True):
        """
        Return all tile matching the characteristics: given tile type
        Used to get a spawning position...
        :param tile_type: the type of tile that we look for
        :param without_objects: set to True to remove objects overlap
        :param region_objects: the list of current game objects
        :param shuffle: if set to True, shuffle before returning the data
        :return: a list of tile positions (tuple)
        """
        listing = []
        entity_pos_listing = set()

        if without_objects:
            for entity in region_objects:
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

    def get_all_available_isolated_tiles(self, tile_type, region_objects, without_objects=False, surrounded=7, max=None, shuffle=True):
        """
        Return all tile matching the characteristics: given tile type, surrounded by 8 cells of same type
        Used to get a spawning position...
        :param tile_type: the types of tile that we look for
        :param without_objects: set to True to remove objects overlap
        :param region_objects: the list of current game objects
        :param surrounded: the number of tiles of same type that the tile should have around
        :return: a list of tile positions (tuple)
        """
        listing = set(self.get_all_available_tiles(tile_type, region_objects, without_objects=without_objects, shuffle=False))
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
                if 0 <= current_position_x + delta_x < self.tile_width and\
                                        0 <= current_position_y + delta_y < self.tile_height:
                    if self.tiles[current_position_x + delta_x][current_position_y + delta_y].tile_type ==\
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
        print("Nb tiles flooded:" + str(len(tiles_flooded)) + " vs to be:" +str(nb_of_tiles_to_be_flooded))
        return nb_of_tiles_to_be_flooded == len(tiles_flooded)


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
                       for y in range(self.tile_height)]
                      for x in range(self.tile_width)]

        reftiles = WildernessRegion._generate_algo(self.tile_width, self.tile_height, 40,
                                                   ((3, 5, 1), (2, 5, -1)), empty_center=False)
        print("Generate base ground ok")
        # Now add some extra stuff depending on the type of map
        # Grass on the floor - to implement we construct a totally new map. We will apply the previous as a mask.
        grass_tile = WildernessRegion._generate_algo(self.tile_width, self.tile_height, 50, ((3, 5, 1), (1, 6, -1)))
        print("Generate grass ground ok")

        # Some shallow Aquatics
        water_tile = []
        if with_liquid:
            water_tile = WildernessRegion._generate_algo(self.tile_width, self.tile_height, 40, ((2, 5, -1),))
            print("Generate shallow liquid ok")

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

        list_available_tiles = self.get_all_available_tiles(Tile.T_GROUND, self.region_entities)
        for town in town_list:
            (town.x, town.y) = list_available_tiles.pop()
            print("Town pos: " + str(town.pos))

        # And we add some path on the floor to connect the towns
        for index_origin, town_origin in enumerate(town_list[:]):
            for index_destination, town_destination in enumerate(town_list[:]):
                if index_destination > index_origin:
                    print("Generating road from {} to {}".format(town_origin.name, town_destination.name))

                    astar = AStar(SQ_MapHandler(self.tiles, dimension[0], dimension[1]))
                    p = astar.findPath(SQ_Location(town_origin.x, town_origin.y),
                                       SQ_Location(town_destination.x, town_destination.y))

                    if p:
                        for n in p.nodes:
                            self.tiles[n.location.x][n.location.y].tile_subtype = Tile.S_PATH

        # Make it a bit more beautiful - warning, needs to be the very last step and may be not usefull...
        #self.remove_extra_blocks()

    @staticmethod
    def _generate_algo(width, height, initial_noise, repeat_parameters, empty_center=False):
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

        initial_seed = random.choice((1, 4, 7, 10))
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

    class Building:
        """
        A building is a closed space, dedicated to a set of activities.
        """
        def __init__(self, size, position=None):
            """
            Initialize the room
            :param size: the size of the room (tuple)
            :param position: The upper left corner of the room (tuple)
            """
            self.size = size
            self.position = position
            self.doors = []
            self.connecting_buildings = []

    def __init__(self, name, dimension, building_list):

        assert dimension[0] % 2 == 1 and dimension[1] % 2 == 1, "Maze dimensions must be odd"
        assert len(building_list) < int(dimension[0]*dimension[1] / 81 * .9), "Too many buildings for the town"

        building_size_range = ((6, 6), (9, 9))
        assert dimension[0] > building_size_range[1][0] \
               and dimension[1] > building_size_range[1][1], "Dimensions too small for even one building"

        Region.__init__(self, name, dimension)

        # Initialize map
        self.tiles = [[Tile(Tile.T_VOID, sub_type=Tile.S_VOID)
                       for y in range(self.tile_height)]
                      for x in range(self.tile_width)]

        # generate the town

        # first building
        self._buildings = {building_list[0]: self._generate_building(building_size_range[0], building_size_range[1])}
        self._place_building(self._buildings[building_list[0]],
                             (int(self.tile_width / 2 - (self._buildings[building_list[0]].size[0] / 2)),
                              int(self.tile_height / 2 - (self._buildings[building_list[0]].size[1] / 2))))

        # all the others
        while len(self._buildings) != len(building_list):
            branching_building = building_list[len(self._buildings)]
            choice_wall = self._get_branching_position_direction(branching_building)
            branching_pos = (choice_wall[0], choice_wall[1])
            branching_dir = choice_wall[2]
            new_building = self._generate_building(building_size_range[0], building_size_range[1])
            path_length = random.choice((0, 2, 3, 5))

            if branching_dir == 'N':
                new_building_pos = (int(branching_pos[0] - (new_building.size[0] / 2)),
                                    int(branching_pos[1] - new_building.size[1] + 1 - path_length))
            elif branching_dir == 'E':
                new_building_pos = (int(branching_pos[0] + path_length),
                                    int(branching_pos[1] - (new_building.size[1] / 2)))
            elif branching_dir == 'S':
                new_building_pos = (int(branching_pos[0] - (new_building.size[0] / 2)),
                                    int(branching_pos[1] + path_length))
            elif branching_dir == 'W':
                new_building_pos = (int(branching_pos[0] - (new_building.size[0]) + 1 - path_length),
                                    int(branching_pos[1] - (new_building.size[1] / 2)))

            if self._space_for_new_building(new_building.size, new_building_pos):
                self._place_building(new_building, new_building_pos)
                self._buildings[branching_building] = new_building
                # Now connecting room
                # No tunnel, easy case:
                new_building.doors.append(branching_pos)
                self._make_floor(branching_pos[0], branching_pos[1])
                new_building.connecting_buildings.append(branching_building)
                branching_building.connecting_buildings.append(new_building)
                # We now place the tunnel
                if branching_dir == 'N':
                    for i in range(1, path_length + 1):
                        self._make_floor(branching_pos[0], branching_pos[1] - i)
                        self._make_wall(branching_pos[0] - 1, branching_pos[1] - i)
                        self._make_wall(branching_pos[0] + 1, branching_pos[1] - i)
                    if path_length >= 3:
                        branching_building.doors.append((branching_pos[0], branching_pos[1] - path_length))
                elif branching_dir == 'E':
                    for i in range(1, path_length + 1):
                        self._make_floor(branching_pos[0] + i, branching_pos[1])
                        self._make_wall(branching_pos[0] + i, branching_pos[1] - 1)
                        self._make_wall(branching_pos[0] + i, branching_pos[1] + 1)
                    if path_length >= 3:
                        branching_building.doors.append((branching_pos[0] + path_length, branching_pos[1]))
                elif branching_dir == 'S':
                    for i in range(1, path_length + 1):
                        self._make_floor(branching_pos[0], branching_pos[1] + i)
                        self._make_wall(branching_pos[0] - 1, branching_pos[1] + i)
                        self._make_wall(branching_pos[0] + 1, branching_pos[1] + i)
                        if path_length >= 3:
                            branching_building.doors.append((branching_pos[0], branching_pos[1] + path_length))
                elif branching_dir == 'W':
                    for i in range(1, path_length + 1):
                        self._make_floor(branching_pos[0] - i, branching_pos[1])
                        self._make_wall(branching_pos[0] - i, branching_pos[1] - 1)
                        self._make_wall(branching_pos[0] - i, branching_pos[1] + 1)
                    if path_length >= 3:
                        branching_building.doors.append((branching_pos[0] - path_length, branching_pos[1]))

    def _generate_building(self, min_size, max_size, modulo_rest=2):
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
        return TownRegion.Building((size_x, size_y))

    def _place_building(self, building, grid_position):
        building.position = grid_position
        for y in range(grid_position[1], grid_position[1] + building.size[1]):
            for x in range(grid_position[0], grid_position[0] + building.size[0]):
                # self.tiles[x][y].room = building
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

    def _space_for_new_building(self, new_building_size, new_building_position, tiles_blocking=Tile.T_GROUND):
        for y in range(new_building_position[1],
                       new_building_position[1] + new_building_size[1]):
            for x in range(new_building_position[0],
                           new_building_position[0] + new_building_size[0]):
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