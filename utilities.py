import os
import pygame as pg
from default import *
import random as rd
# Set of utilities


def roll(dice, repeat=1):
    """
    Roll one or multiple dice(s)
    :param dice: the type of dice - 6 for d6, 8 for d8...
    :param repeat: the number of dices of same tye to roll
    :return: the value
    """
    res = 0
    for i in range(repeat):
        res += rd.randint(1, dice)
    return res


class Ticker(object):
    """Simple timer for roguelike games."""

    def __init__(self):
        self.ticks = 0  # current ticks--sys.maxint is 2147483647
        self.schedule = {}  # this is the dict of things to do {ticks: [obj1, obj2, ...], ticks+1: [...], ...}
        self.ticks_to_advance = 0

    def schedule_turn(self, interval, obj):
        self.schedule.setdefault(self.ticks + interval, []).append(obj)

    def _advance_ticks(self, interval):
        for i in range(interval):
            things_to_do = self.schedule.pop(self.ticks, [])
            for obj in things_to_do:
                if obj is not None:
                    obj.take_turn()
            self.ticks += 1

    def advance_ticks(self):
        if self.ticks_to_advance > 0:
            self._advance_ticks(self.ticks_to_advance)
            self.ticks_to_advance = 0

    def unregister(self, obj):
        if obj is not None:
            for key in self.schedule.keys():
                while obj in self.schedule[key]:
                    self.schedule[key].remove(obj)


class Publisher(object):
    """
    Dispatch messages
    Messages have two categories (defined in constants):
    * Main: like log, fight, exploration, inventory
    * Sub: precises the main, optional.
    Messgae content is a dictionary
    """
    CATEGORY_ALL = "*"

    def __init__(self):
        self._specialized_list = {}  # Subscribe to main and a list of sub_category
        self.in_publish = False
        self.delayed_unregister = []

    def register(self,
                 object_to_register,
                 main_category=CATEGORY_ALL,
                 sub_category=CATEGORY_ALL,
                 function_to_call=None):
        """
        Register an object so that we can pass him an object
        :param object_to_register: the object that will be notified.
        Note that the same object may be registered multiple time, with different functions to be called or
        different category of interest, so that we are effectively saving the method only
        :param main_category: one or multiple (in list) categories to register.
        :param sub_category: one or multiple (in list) specialized sub categories to register
        :param function_to_call: the method to be called.
        :return:
        """
        if function_to_call is None:
            assert hasattr(object_to_register, "notify"), \
                "Object {} has no notify method and has not precised the " \
                "function to be called".format(object_to_register)
            function_to_call = getattr(object_to_register, "notify")
        if type(sub_category) is not (list or tuple):
            sub_category = [sub_category]
        if type(main_category) is not (list or tuple):
            main_category = [main_category]
        for category in main_category:
            for sub in sub_category:
                key = "{}#{}".format(category, sub)
                if key not in self._specialized_list.keys():
                    self._specialized_list[key] = [function_to_call]
                elif function_to_call not in self._specialized_list[key]:
                    self._specialized_list[key].append(function_to_call)

    def unregister_all(self, object_to_unregister):
        # We need to parse all the lists..
        # and the same object may have been registered with different functions
        if self.in_publish:
            self.delayed_unregister.append(object_to_unregister)
        else:
            for key in self._specialized_list.keys():
                list_to_remove = []
                list_to_parse = self._specialized_list[key]
                for function_called in list_to_parse:
                    if function_called.__self__ == object_to_unregister:
                        list_to_remove.append(function_called)
                for function_called in list_to_remove:
                    self._specialized_list[key].remove(function_called)

    def handle_delayed_unregister_all(self):
        for object_to_unregister in self.delayed_unregister:
            self.unregister_all(object_to_unregister)

    def publish(self, source, message, main_category=CATEGORY_ALL, sub_category=CATEGORY_ALL):
        self.in_publish = True
        assert type(message) is dict, "Message {} is not a dict".format(message)
        message["SOURCE"] = source
        broadcasted_list = []
        message["MAIN_CATEGORY"] = main_category
        message["SUB_CATEGORY"] = sub_category
        if type(sub_category) is not (list or tuple):
            sub_category = [sub_category]
        if type(main_category) is not (list or tuple):
            main_category = [main_category]

        # By default, we always broadcast to "ALL"
        if Publisher.CATEGORY_ALL not in main_category:
            main_category.append(Publisher.CATEGORY_ALL)
        if Publisher.CATEGORY_ALL not in sub_category:
            sub_category.append(Publisher.CATEGORY_ALL)

        for category in main_category:
            for sub in sub_category:
                message["BROADCAST_MAIN_CATEGORY"] = category
                message["BROADCAST_SUB_CATEGORY"] = category
                key = "{}#{}".format(category, sub)
                if key in self._specialized_list:
                    for function_called in self._specialized_list[key]:
                        if function_called not in broadcasted_list:  # Need to be sure not to send two times the message
                            function_called(message)
                            broadcasted_list.append(function_called)
        self.in_publish = False
        self.handle_delayed_unregister_all()


class Logger:

    ERROR = 5
    WARN = 4
    INFORM = 3
    DEBUG = 2
    TRACE = 1
    LABELS = ("", "[TRACE] ", "[DEBUG] ", "[INFORM] ","[WARN] ", "[ERROR] ")

    def __init__(self):
        self._log_level = Logger.TRACE

    def log(self, message, level=INFORM):
        if level >= self._log_level:
            self.out(Logger.LABELS[level] + message)

    def out(self, message):
        print(message)

    def handle_published_message(self, message):
        self.out("[MESSAGE] " + message)

    def trace(self, message):
        self.log(message, level=Logger.TRACE)

    def debug(self, message):
        self.log(message, level=Logger.DEBUG)

    def inform(self, message):
        self.log(message, level=Logger.INFORM)

    def warn(self, message):
        self.log(message, level=Logger.WARN)

    def error(self, message):
        self.log(message, level=Logger.ERROR)


class EmptyLogger(Logger):

    def out(self, message):
        pass

    def handle_published_message(self, message):
        pass


# Graphical utilities
def get_image(image_src_list, folder, image_name):
    key = str(folder) + image_name
    if key not in image_src_list:
        image_src_list[key] = pg.image.load(os.path.join(folder, image_name)).convert_alpha()
    return image_src_list[key]


def load_image(image_src_list, folder, image_name, tile_x, tile_y, width=16, height=16, adapt_ratio=1):
    """
    Load a single image from a file and put it in the image dictionnary
    :param image_src_list: the image dictionnary that will be modified
    :param folder: the folder from which the image needs to be loaded
    :param image_name: the name of the file to be loaded
    :param tile_x: the position in the file of the sub part to be loaded (x)
    :param tile_y: the position in the file of the sub part to be loaded (y)
    :param width: the dimension of a tile
    :param height: th edimension of a tile
    :return:
    """
    image_src = get_image(image_src_list, folder, image_name)
    if adapt_ratio is None:
        return image_src.subsurface(pg.Rect(width * tile_x, height * tile_y, width, height))
    elif width == TILESIZE_SCREEN[0] * adapt_ratio and height == TILESIZE_SCREEN[1] * adapt_ratio:
        return image_src.subsurface(pg.Rect(width * tile_x, height * tile_y, width, height))
    else:
        return pg.transform.scale(image_src.subsurface(pg.Rect(width * tile_x, height * tile_y, width, height)),
                                  (int(TILESIZE_SCREEN[0] * adapt_ratio), int(TILESIZE_SCREEN[1] * adapt_ratio)))


def load_image_list_dawnlike(image_src_list, folder, image_name1, image_name2, tile_x, tile_y,
                             width=16, height=16):
    """
    Load an image list from two different files following dawnlike approach
    :param image_src_list: the actual dictionary that may already contain the source
    :param img_folder_name: the folder where images are located
    :param image1: the first image file name
    :param image2: the second image file name
    :param tile_x: th etile position - note that
    :param tile_y:
    :param width:
    :param height:
    :return: a list of two images
    """
    image_src1 = get_image(image_src_list, folder, image_name1)
    image_src2 = get_image(image_src_list, folder, image_name2)

    if width == TILESIZE_SCREEN[0] and height == TILESIZE_SCREEN[1]:
        return [image_src1.subsurface(pg.Rect(width * tile_x, height * tile_y, width, height)),
                image_src2.subsurface(pg.Rect(width * tile_x, height * tile_y, width, height))]
    else:
        return [pg.transform.scale(image_src1.subsurface(pg.Rect(width * tile_x, height * tile_y, width, height)),
                                   TILESIZE_SCREEN),
                pg.transform.scale(image_src2.subsurface(pg.Rect(width * tile_x, height * tile_y, width, height)),
                                   TILESIZE_SCREEN)]


def load_wall_structure_dawnlike(image_src_list, folder, image_name):
    """
    Load the set of walls from dawnlike file
    :param image_src_list: the actual dictionary that may already contain the source
    :param image_src:
    :return: a list of dictionary item following convention
    http://www.angryfishstudios.com/2011/04/adventures-in-bitmasking/
    """
    image_src = get_image(image_src_list, folder, image_name)
    image_set = []
    ref_tuples = {0: (1, 1), 1: (1, 1),
                  2: (1, 0), 3: (0, 2),
                  4: (0, 1), 5: (0, 1),
                  6: (0, 0), 7: (3, 1),
                  8: (1, 0), 9: (2, 2),
                  10: (1, 0), 11: (4, 2),
                  12: (2, 0), 13: (5, 1),
                  14: (4, 0), 15: (4, 1)}
    for line in range(16):
        for column in range(2):
            top_x = column * (7 * 16)
            top_y = line * (3 * 16) + 3 * 16
            dict_image = {}
            for key in ref_tuples:
                delta_x = ref_tuples[key][0] * 16 + top_x
                delta_y = ref_tuples[key][1] * 16 + top_y
                dict_image[key] = pg.transform.scale(image_src.subsurface(pg.Rect(delta_x, delta_y, 16, 16)),
                                                     TILESIZE_SCREEN)
            image_set.append(dict_image)
    return image_set


def load_floor_structure_dawnlike(image_src_list, folder, image_name):
    """
    Load the set of walls from dawnlike file and put it in a dictionary
    :param image_src_list: the actual dictionary that may already contain the source
    :param folder: the folder from which the image will be loaded
    :param the name of teh image file
    :return: a list of dictionary item following convention
    http://www.angryfishstudios.com/2011/04/adventures-in-bitmasking/
    """
    image_src = get_image(image_src_list, folder, image_name)
    image_set = []
    ref_tuples = {0: (5, 0), 1: (3, 2),
                  2: (4, 1), 3: (0, 2),
                  4: (3, 0), 5: (3, 1),
                  6: (0, 0), 7: (0, 1),
                  8: (6, 1), 9: (2, 2),
                  10: (5, 1), 11: (1, 2),
                  12: (2, 0), 13: (2, 1),
                  14: (1, 0), 15: (1, 1)}
    for line in range(8):
        for column in range(3):
            top_x = column * (7 * 16)
            top_y = line * (3 * 16) + 3 * 16
            dict_image = {}
            for key in ref_tuples:
                delta_x = ref_tuples[key][0] * 16 + top_x
                delta_y = ref_tuples[key][1] * 16 + top_y
                dict_image[key] = pg.transform.scale(image_src.subsurface(pg.Rect(delta_x, delta_y, 16, 16)),
                                                     TILESIZE_SCREEN)
            image_set.append(dict_image)
    return image_set


def _load_player(image_src_list, folder, image_name, width=16, height=16):
    result = {"S": [load_image(image_src_list, folder, image_name, i, 0, width=width, height=height) for i in range(4)],
              "W": [load_image(image_src_list, folder, image_name, i, 1, width=width, height=height) for i in range(4)],
              "E": [load_image(image_src_list, folder, image_name, i, 2, width=width, height=height) for i in range(4)],
              "N": [load_image(image_src_list, folder, image_name, i, 3, width=width, height=height) for i in range(4)]}
    return result


def load_all_images():

    images = {}  # the actual list of images to be built
    image_src_list = {}  # a cache for objects

    # Folder: Player
    images["PLAYER_ENGINEER"] = _load_player(image_src_list, PLAYER_FOLDER, "Engineer.png")
    images["PLAYER_MAGE"] = _load_player(image_src_list, PLAYER_FOLDER, "Mage.png")
    images["PLAYER_PALADIN"] = _load_player(image_src_list, PLAYER_FOLDER, "Paladin.png")
    images["PLAYER_ROGUE"] = _load_player(image_src_list, PLAYER_FOLDER, "Rogue.png")
    images["PLAYER_WARRIOR"] = _load_player(image_src_list, PLAYER_FOLDER, "Warrior.png")

    # Folder: Objects
    # Floor & Wall
    images["FLOOR"] = load_floor_structure_dawnlike(image_src_list, OBJECT_FOLDER, "Floor.png")
    images["WALLS"] = load_wall_structure_dawnlike(image_src_list, OBJECT_FOLDER, "Wall.png")
    # Doors
    images["DOOR_V_OPEN"] = load_image(image_src_list, OBJECT_FOLDER, "Door1.png", 1, 0)
    images["DOOR_V_CLOSED"] = load_image(image_src_list, OBJECT_FOLDER, "Door0.png", 1, 0)
    images["DOOR_H_OPEN"] = load_image(image_src_list, OBJECT_FOLDER, "Door1.png", 0, 0)
    images["DOOR_H_CLOSED"] = load_image(image_src_list, OBJECT_FOLDER, "Door0.png", 0, 0)
    # Stairs
    images["STAIRS"] = load_image(image_src_list, OBJECT_FOLDER, "Tile.png", 1, 1)

    return images
