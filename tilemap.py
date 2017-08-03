import pygame as pg
import random
from os import path
import utilities
from default import *
from shared import GLOBAL


class Tile:
    """
    A tile of the map and its properties
    """
    # Main types
    T_VOID = '0'
    T_BORDER = '1'  # Might be the wall of a grotto or of a room, trees or boulders
    T_FLOOR = '2'  # Generic - can be grass as well.
    T_LIQUID = '3'  # A specific division of the floor

    # Sub Types
    S_VOID = '0_0'
    # Border
    S_TREE = '1_1'
    S_WALL = '1_2'
    S_BOULDER = '1_3'
    # Floor
    S_FLOOR = '2_0'  # Regular dirt
    S_PATH = '2_1'
    S_GRASS = '2_2'
    S_CARPET = '2_3'
    # Liquid
    S_WATER = '3_1'  # Only Aquatics will be able to cross
    S_LAVA = '3_2'

    def __init__(self, tile_type=T_VOID, sub_type=S_VOID, room=None):
        self.tile_type = tile_type
        self.tile_subtype = sub_type
        self.explored = False
        self.room = room

    def block_for(self, entity):
        if entity.blocking_tile_list:
            if self.tile_type in entity.blocking_tile_list:
                return True
            else:
                return False
        elif self.tile_type in (Tile.T_VOID, Tile.T_BORDER):  # Default blocking list
            return True
        return False

    def block_view_for(self, entity):
        if hasattr(entity, "blocking_view_tile_list"):
            if self.tile_type in entity.blocking_view_tile_list:
                return True
            else:
                return False
        elif self.tile_type in (Tile.T_VOID, Tile.T_BORDER):  # Default blocking list
            return True
        return False


class DungeonMapFactory:
    """
    Used to generate one of the predefined map type
    """

    MAP_TYPE_CELLULAR = "CELLULAR"
    MAP_TYPE_DUNGEON = "DUNGEON"

    def __init__(self,
                 name,
                 state=None,
                 map_type=None,
                 map_subtype=None,
                 filename=None,
                 dimension=(81, 121)):
        """

        :param name: The name of the map. Can be used as a future reference
        :param state: All maps are generated using random things. This is to define the seed of the map.
        :param filename: Use to generate the map from a file representation
        :param dimension: The dimension of the map
        :param map_type: Type of the map. So far, can be CELLULAR for Cellular Family or DUNGEON for Dungeon Family
        :param map_subtype: Subtype of the map. For Cellular, can be SURFACE (Tree, water, grass...) or GROTTO (Walls, lava,
        """
        if state is not None:
            random.setstate(state)
        self.state = random.getstate()

        map_correctly_initialized = False
        self.map = None

        if filename is not None:
            # self.map = FileMap(name, filename)
            pass
        else:
            while not map_correctly_initialized:
                print(" *** GENERATING MAP *** ")
                map_type = utilities.roll(4)
                self.map = CellularMap(name, dimension, CellularMap.TYPE_FOREST)

                '''
                if map_type == 1:
                    self.map = CaveMap(name, dimension)
                elif map_type == 2:
                    self.map = RoomAndMazeMap(name, dimension)
                elif map_type == 3:
                    self.map = MazeMap(name, dimension)
                else:
                    self.map = RoomMap(name, dimension)
                '''
                map_correctly_initialized = self.map.is_valid_map()

        # Make it a bit more beautiful
        # self.map.remove_extra_walls()

        # TODO: remove teh following
        self.map._build_background("Test.png")


class Map:
    """
    The Map, representing a level.
    Mainly holds a reference to a set of tiles, as well as dimensions.
    """

    def __init__(self, name, dimension):

        self.name = name
        self._background = None

        self.tile_width = dimension[0]  # width of map, expressed in tiles
        self.tile_height = dimension[1]  # height of map, expressed in tiles

        self.tiles = []
        self.rooms = []
        self._doors_pos = None

        self.wall_ref_number = random.randint(0, len(GLOBAL.img('WALLS')) - 1)  # we keep this as a ref for later

    @property
    def background(self):
        if self._background is None:
            self._build_background()
        return self._background

    @property
    def doors_pos(self):
        if self._doors_pos is None:
            self._doors_pos = set()
            for room in self.rooms:
                for door in room.doors:
                    if door not in self._doors_pos:
                        self._doors_pos.add(door)
        return self._doors_pos

    def clean_before_save(self):
        self._background = None

    def remove_extra_walls(self):
        """
        Generic method used by all to clean up after generation
        """
        for x in range(0, self.tile_width):
            for y in range(0, self.tile_height):
                if self.tiles[x][y].tile_type == Tile.T_BORDER:
                    delta = [(0, -1), (0, 1), (1, 0), (-1, 0), (1, 1), (-1, -1), (1, -1), (-1, 1)]
                    count = 0
                    for (dx, dy) in delta:
                        if x + dx < 0 or x + dx >= self.tile_width or y + dy < 0 or y + dy >= self.tile_height:
                            count += 1
                        elif self.tiles[x + dx][y + dy].tile_type in (Tile.T_BORDER, Tile.T_VOID):
                            count += 1
                    if count == 8:
                        self.tiles[x][y].tile_type = Tile.T_VOID

    def tile_weight(self, x, y, door_list, tile_type=(Tile.T_BORDER)):
        """
        Taken from http://www.angryfishstudios.com/2011/04/adventures-in-bitmasking/
        :param x:
        :param y:
        :param door_list: current list of doors
        :param tile_type: the tyle type used as reference
        :return:
        """
        weight = 0
        if (y - 1 >= 0 and (self.tiles[x][y - 1].tile_type in tile_type or (x, y - 1) in door_list)) or y == 0:
            weight += 1
        if (x - 1 >= 0 and (self.tiles[x - 1][y].tile_type in tile_type or (x - 1, y) in door_list)) or x == 0:
            weight += 8
        if (y + 1 < self.tile_height and (self.tiles[x][y + 1].tile_type in tile_type or (x, y + 1) in door_list)) or \
                        y == self.tile_height - 1:
            weight += 4
        if (x + 1 < self.tile_width and (self.tiles[x + 1][y].tile_type in tile_type or (x + 1, y) in door_list)) or \
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

    def get_random_available_tile(self, tile_type, game_objects, without_objects=True):
        """
        Return a tile matching the characteristics: given tile type
        Used to get a spawning position...
        By default, the tile should be without objects and out of any doors position
        :param tile_type: the type of tile that we look for
        :param without_objects: check if no objects is there, and that it is not a possible door position
        :param game_objects: the list of current objects in the game
        :return: a tile position (tuple)
        """
        entity_pos_listing = set()

        if without_objects:
            for entity in game_objects:
                entity_pos_listing.add((entity.x, entity.y))

        while True:
            x = random.randint(0, self.tile_width - 1)
            y = random.randint(0, self.tile_height - 1)
            if self.tiles[x][y].tile_type == tile_type:
                if without_objects and ((x, y) not in entity_pos_listing and (x, y) not in self.doors_pos):
                    return x, y
                elif (x, y) not in self.doors_pos:
                    return x, y

    def get_close_available_tile(self, ref_pos, tile_type, game_objects, without_objects=True):
        """
        Return a tile matching the characteristics: given tile type near entity
        By default, the tile should be without objects and out of any doors position
        :param ref_pos: the ref position for the object
        :param tile_type: the type of tile that we look for
        :param without_objects: check if no objects is there, and that it is not a possible door position
        :param game_objects: the list of current objects in the game
        :return: a tile position (tuple) that matches free, the ref pos if none is found
        """
        entity_pos_listing = set()

        if without_objects:
            for entity in game_objects:
                entity_pos_listing.add((entity.x, entity.y))

        delta = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]
        random.shuffle(delta)
        pos_x, pos_y = ref_pos

        for d in delta:
            x = pos_x + d[0]
            y = pos_y + d[1]
            if self.tiles[x][y].tile_type == tile_type:
                if without_objects and ((x, y) not in entity_pos_listing and (x, y) not in self.doors_pos):
                    return x, y
                elif (x, y) not in self.doors_pos:
                    return x, y
        return ref_pos

    def get_all_available_tiles(self, tile_type, game_objects, without_objects=False):
        """
        Return all tile matching the characteristics: given tile type
        Used to get a spawning position...
        :param tile_type: the type of tile that we look for
        :param without_objects: set to True to remove objects overlap
        :param game_objects: the list of current game objects
        :return: a list of tile positions (tuple)
        """
        listing = []
        entity_pos_listing = set()

        if without_objects:
            for entity in game_objects:
                entity_pos_listing.add((entity.x, entity.y))

        for x in range(self.tile_width):
            for y in range(self.tile_height):
                if self.tiles[x][y].tile_type in tile_type:
                    if without_objects:
                        if (x, y) not in entity_pos_listing and (x, y) not in self.doors_pos:
                            listing.append((x, y))
                    else:
                        listing.append((x, y))
        random.shuffle(listing)
        return listing

    def get_all_available_isolated_tiles(self, tile_type, game_objects, without_objects=False, surrounded=7, max=None):
        """
        Return all tile matching the characteristics: given tile type, surrounded by 8 cells of same type
        Used to get a spawning position...
        :param tile_type: the types of tile that we look for
        :param without_objects: set to True to remove objects overlap
        :param game_objects: the list of current game objects
        :param surrounded: the number of tiles of same type that the tile should have around
        :return: a list of tile positions (tuple)
        """
        listing = set(self.get_all_available_tiles(tile_type, game_objects, without_objects=without_objects))
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
        return result

    def get_room_at(self, x, y):
        if hasattr(self, "rooms"):
            for room in self.rooms:
                if (x, y) in room.get_tile_list():
                    return room
        return None

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
            self._build_background_dawnlike()

        if name is not None:
            pg.image.save(self._background, path.dirname(__file__) + '/' + name)

    def _build_background_dawnlike(self):
        """
        Build background using dawnlike tileset
        :return: Nothing, just blitting things on _background property
        """
        # First, we choose our wall serie
        wall_series = random.randint(0, len(GLOBAL.img('WALLS')) - 1)
        floor_series = random.randint(0, len(GLOBAL.img('FLOOR')) - 1)

        for y in range(self.tile_height):
            for x in range(self.tile_width):

                door_list = []
                # build door list - except if we are in a pure maze
                if hasattr(self, "rooms") and self.rooms is not None:
                    for room in self.rooms:
                        for door_pos in room.doors:
                            door_list.append(door_pos)
                weight_wall = self.tile_weight(x, y, door_list)
                weight_floor = self.tile_weight(x, y, door_list, tile_type=Tile.T_FLOOR)

                if self.tiles[x][y].tile_type == Tile.T_BORDER:
                    # We always blit a floor... but using the wall as reference for weight
                    self._background.blit(GLOBAL.img('FLOOR')[floor_series][weight_wall],
                                          (x * TILESIZE_SCREEN[0], y * TILESIZE_SCREEN[1]))
                    self._background.blit(GLOBAL.img('WALLS')[wall_series][weight_wall],
                                          (x * TILESIZE_SCREEN[0], y * TILESIZE_SCREEN[1]))
                elif self.tiles[x][y].tile_type == Tile.T_FLOOR:
                    self._background.blit(GLOBAL.img('FLOOR')[floor_series][weight_floor],
                                          (x * TILESIZE_SCREEN[0], y * TILESIZE_SCREEN[1]))

    def check_all_tile_connected(self, starting_type_type = Tile.T_FLOOR):
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

        print("Size of flood = " + str(len(tiles_flooded)))
        print("Goal = " + str(nb_of_tiles_to_be_flooded))
        return nb_of_tiles_to_be_flooded == len(tiles_flooded)

    def is_valid_map(self):
        all_size = int(self.tile_width * self.tile_height)

        map_correctly_initialized = \
            len(self.get_all_available_tiles(Tile.T_FLOOR, [], without_objects=True)) > int(all_size / 4)
        return map_correctly_initialized


class CellularMap(Map):
    """
    A map which is based on a cellular automaton
    This map can be used for:
    - Grotto type: ground is dark. Borders are made of hills. Not a lot of smoothing, so the algo is stopped very
    quickly (in the repeat). If there is liquid (Pit) it is lava style.
    - Surface Town: ground can be dirt or grass. Borders are made of trees. Very smooth, at least 6 repetition to get
    large surface of ground.
    - Subterran Town:
    - Forest type: ground is lighter, with dirt or grass. Borders are made of trees. Not a lot of smoothing. Liquid is
    made of Water (pit)
    - Aquatic: the border is replaced by water from the Pit
    """
    TYPE_GROTTO = "Grotto"
    TYPE_FOREST = "Forest"
    TYPE_SURFACE_TOWN = "Town_surface"
    TYPE_SUBTERRAN_TOWN = "Town_under"
    TYPE_AQUATIC_TOWN = "Town_aquatic"

    def __init__(self,
                 name,
                 dimension,
                 map_type,
                 with_liquid=False):

        assert dimension[0] % 2 == 1 and dimension[1] % 2 == 1, "Maze dimensions must be odd"
        Map.__init__(self, name, dimension)  # dimensions doivent être impair!

        self.tiles = [[Tile(Tile.T_FLOOR, sub_type=Tile.S_FLOOR)
                       for y in range(self.tile_height)]
                      for x in range(self.tile_width)]

        reftiles = CellularMap._generate_algo(self.tile_width, self.tile_height, 40, ((3,5,1),(2,5,-1)), empty_center=True)

        for y in range(self.tile_height):
            for x in range(self.tile_width):
                if reftiles[x][y] == 1:
                    self.tiles[x][y].tile_type = Tile.T_BORDER

        # Now add some extra stuff depending on the type of map
        # Grass on the floor - to implement we construct a totally new map. We will apply the previous as a mask.
        # Now we add some rooms
        # And we add some path on the floor to connect teh room
        # Some Aquatics - must be on non blocking and not on path!
        # Some Extra Blocks like trees or boulders

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
                        count = CellularMap._count_border_tile(tiles, x, y, 1)
                        if count >= number_to_keep:
                            tiles[x][y] = 1
                        elif number_to_be_born >= 0 and count <= number_to_be_born:
                            tiles[x][y] = 1
                        else:
                            tiles[x][y] = 0

        if empty_center:
            CellularMap._eliminate_center_border(tiles, width, height)  # A bit brutal
            for y in range(1, height - 1):  # We smooth a bit the result
                for x in range(1, width - 1):
                    count = CellularMap._count_border_tile(tiles, x, y, 1)
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


    def _build_background_dawnlike(self):
        """
        Build background using dawnlike tileset - Redefined here
        :return: Nothing, just blitting things on _background property
        """
        # First, we choose our wall serie
        wall_series = random.randint(0, len(GLOBAL.img('WALLS')) - 1)
        floor_series = random.randint(0, len(GLOBAL.img('FLOOR')) - 1)
        tree_series = random.randint(0, len(GLOBAL.img('TREES')) - 1)

        for y in range(self.tile_height):
            for x in range(self.tile_width):

                door_list = []
                # build door list - except if we are in a pure maze
                if hasattr(self, "rooms") and self.rooms is not None:
                    for room in self.rooms:
                        for door_pos in room.doors:
                            door_list.append(door_pos)
                weight_wall = self.tile_weight(x, y, door_list)
                weight_floor = self.tile_weight(x, y, door_list, tile_type=Tile.T_FLOOR)

                if self.tiles[x][y].tile_type == Tile.T_BORDER:
                    # We always blit a floor... but using the wall as reference for weight
                    self._background.blit(GLOBAL.img('FLOOR')[floor_series][weight_wall],
                                          (x * TILESIZE_SCREEN[0], y * TILESIZE_SCREEN[1]))
                    #self._background.blit(GLOBAL.img('WALLS')[wall_series][weight_wall],
                    #                      (x * TILESIZE_SCREEN[0], y * TILESIZE_SCREEN[1]))
                    self._background.blit(GLOBAL.img('TREES')[tree_series][weight_wall],
                                          (x * TILESIZE_SCREEN[0], y * TILESIZE_SCREEN[1]))
                elif self.tiles[x][y].tile_type == Tile.T_FLOOR:
                    self._background.blit(GLOBAL.img('FLOOR')[floor_series][weight_floor],
                                          (x * TILESIZE_SCREEN[0], y * TILESIZE_SCREEN[1]))

    def is_valid_map(self):
        return Map.is_valid_map(self) and self.check_all_tile_connected()
