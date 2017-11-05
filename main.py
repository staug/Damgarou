import os
import sys

import pygame as pg
import thorpy
import random
import dill as pick


import default
from entity.player import Player
from entity.town import Entrance, Bank, GuildFighter, GuildMule, Shop, Tavern, Trade, Townhall, Temple
from gui import guiwidget
from gui.screen import PlayingScreen, BuildingScreen
from region.region import RegionFactory
from shared import GLOBAL
from utilities import MName


class Game:

    GAME_STATE_PLAYING = 'Playing'
    GAME_STATE_INVENTORY = 'Inventory'
    GAME_STATE_MAP = 'Map'
    GAME_STATE_CHARACTER = 'Character'
    GAME_STATE_BUILDING = 'Building'

    def __init__(self):

        self.game_state = Game.GAME_STATE_PLAYING
        self.player_took_action = False
        self.minimap_enabled = False
        self.game_running = True
        self.screens = {Game.GAME_STATE_PLAYING: PlayingScreen(), Game.GAME_STATE_BUILDING: BuildingScreen()}
        self.current_region = None
        self.player = None
        self.invalidate_fog_of_war = True

        self.world = {}  # The world contains all the wilderness regions and all towns

    def new(self):

        guiwidget.display_single_message_on_screen("Generating World")

        guiwidget.display_single_message_on_screen("Generating World - Wilderness")
        player_spawn_pos = None  # this will be a town on a wilderness

        for _i in range(1):
            name = MName.place_name()
            town_list = []
            for _j in range(random.randint(2, 6)):
                name_town = "{}'s Town".format(MName.person_name())
                town_region = RegionFactory.invoke(name_town,
                                                   wilderness_index=name,
                                                   region_type=RegionFactory.REGION_TOWN,
                                                   building_list=(Entrance(),
                                                                  Bank(),
                                                                  GuildMule(),
                                                                  GuildFighter(),
                                                                  Shop(),
                                                                  Tavern(), Trade(), Townhall(), Temple()))
                town_list.append(town_region)
                self.world[name_town] = town_region

            self.world[name] = RegionFactory.invoke(name,
                                                    region_type=RegionFactory.REGION_WILDERNESS,
                                                    town_list=town_list)
            player_spawn_pos = town_list[0].town.pos  # small hack

        guiwidget.display_single_message_on_screen("World ok")

        self.current_region = self.world[name]
        # We start the player, and we add it at his spawning position (a town of hte latest wilderness)
        self.player = Player()
        self.player.assign_entity_to_region(self.current_region)
        (self.player.x, self.player.y) = player_spawn_pos

    def start(self):
        self.run()

    def run(self):
        clock = pg.time.Clock()

        while self.game_running:
            self.screens[self.game_state].events()
            self.screens[self.game_state].update()
            self.screens[self.game_state].draw()
            clock.tick(40)  # the program will never run at more than 40 frames per second

    def reinit_graphics_after_save(self):
        for region_name in self.world:
            for entity in self.world[region_name].region_entities:
                entity.init_graphics()

    def clean_graphics_before_save(self):
        for region_name in self.world:
            for entity in self.world[region_name].region_entities:
                entity.clean_before_save()
            self.world[region_name].clean_before_save()

    @staticmethod
    def quit():
        pg.quit()
        sys.exit()


class Launcher:
    """
    Initialize the system
    Start the game interface
    Open a menu with a choice to start a new game, load one, parameter or quit
    """

    def __init__(self):
        self.widgets = None
        Launcher.init_pygame_subsystem()
        Launcher.load_data()
        self.launcher_running = True

    @staticmethod
    def init_pygame_subsystem():
        GLOBAL.logger.trace("Initializing Pygame")
        pg.display.init()
        pg.font.init()
        pg.display.set_mode((default.GAME_WIDTH, default.GAME_HEIGHT), pg.RESIZABLE)
        pg.display.set_caption(default.GAME_TITLE + "-" + default.GAME_VER)
        thorpy.set_theme("human")
        GLOBAL.logger.trace("Initializing Pygame - Done")

    @staticmethod
    def load_data():
        GLOBAL.logger.trace("Loading Images")
        GLOBAL.load_images()
        GLOBAL.logger.trace("Loading Images - Done")

    def implement_menu(self):

        font = pg.font.Font(os.path.join(default.FONT_FOLDER, default.FONT_NAME), 18)

        button_start = thorpy.make_button("Start", func=self.start)
        button_start.set_size((100, None))
        button_start.set_font(font)
        button_start.set_font_size(16)

        button_load = thorpy.make_button("Load", func=self.load)
        button_load.set_size((100, None))
        button_load.set_font(font)
        button_load.set_font_size(16)

        button_quit = thorpy.make_button("Quit", func=Launcher.quit)
        button_quit.set_size((100, None))
        button_quit.set_font(font)
        button_quit.set_font_size(16)

        box = thorpy.Box.make(elements=[button_start,
                                        button_load,
                                        button_quit])
        box.set_main_color((0, 0, 0, 0))

        self.widgets = thorpy.Menu(box)
        for element in self.widgets.get_population():
            # Note: assume that the pygame.display.set_mode() was called before
            element.surface = pg.display.get_surface()

        box.set_center(pg.display.get_surface().get_rect().center)

        box.blit()
        box.update()

    def run(self):
        self.implement_menu()
        while self.launcher_running:
            for event in pg.event.get():
                if event.type == pg.QUIT:
                    Launcher.quit()
                self.widgets.react(event)

    def start(self):
        self.launcher_running = False
        GLOBAL.game = Game()
        GLOBAL.game.new()
        GLOBAL.game.start()

    def load(self):
        self.launcher_running = False
        with open("savegame", "rb") as f:
            GLOBAL.game = pick.load(f)[0]
            GLOBAL.game.reinit_graphics_after_save()

        # Done: starting the game
        self.widgets = []  # Killing the menu. A bit forced, but prevent some problems.
        GLOBAL.game.start()

    @staticmethod
    def quit():
        pg.quit()
        sys.exit()


if __name__ == '__main__':
    Launcher().run()
