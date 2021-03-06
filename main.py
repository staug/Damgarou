# import random
import sys

import dill as pick
import pygame as pg

import default
from gui.buildingscreen import BuildingScreen
from gui.guicontainer import LineAlignedContainer
from gui.guiwidget import TextButton, Style
from gui.screen import PlayingScreen, PlayerCreationScreen, WorldCreationScreen
from shared import GLOBAL


class Game:
    GAME_STATE_PLAYING = 'Playing'
    GAME_STATE_PLAYER_CREATION = 'Player_Creation'
    GAME_STATE_WORLD_CREATION = 'World_Creation'
    GAME_STATE_INVENTORY = 'Inventory'
    GAME_STATE_MAP = 'Map'
    GAME_STATE_CHARACTER = 'Character'
    GAME_STATE_BUILDING = 'Building'

    def __init__(self):
        self._state = None
        self._switching_state = None

        self.player_took_action = False
        self.minimap_enabled = False
        self.game_running = True
        self.shared_widgets = {
            "TextArea": None
        }
        self.screens = {Game.GAME_STATE_PLAYING: PlayingScreen(),
                        Game.GAME_STATE_PLAYER_CREATION: PlayerCreationScreen(),
                        Game.GAME_STATE_WORLD_CREATION: WorldCreationScreen(),
                        Game.GAME_STATE_BUILDING: BuildingScreen()}

        self.current_region = None
        self.player = None
        self.invalidate_fog_of_war = True

        self.world = {}  # The world contains all the wilderness regions and all towns

    def post_init(self):
        # Post init on screens
        for screen_name in self.screens:
            self.screens[screen_name].post_init()

    def new(self):
        self.update_state(Game.GAME_STATE_PLAYER_CREATION)

    def start(self):
        self.run()

    def run(self):
        clock = pg.time.Clock()

        while self.game_running:
            if self._switching_state is not None:
                self._state = self._switching_state
                self._switching_state = None

            if self._switching_state is None:
                self.screens[self._state].events()
            if self._switching_state is None:
                self.screens[self._state].update()
            if self._switching_state is None:
                self.screens[self._state].draw()
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

    def update_state(self, new_state):
        self._switching_state = new_state

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
        Style.set_style()
        self.implement_menu()

    @staticmethod
    def init_pygame_subsystem():
        GLOBAL.logger.trace("Initializing Pygame")
        pg.display.init()
        pg.font.init()
        pg.display.set_mode((default.GAME_WIDTH, default.GAME_HEIGHT), pg.RESIZABLE)
        pg.display.set_caption(default.GAME_TITLE + "-" + default.GAME_VER)
        GLOBAL.logger.trace("Initializing Pygame - Done")

    @staticmethod
    def load_data():
        GLOBAL.logger.trace("Loading Images")
        GLOBAL.load_images()
        GLOBAL.logger.trace("Loading Images - Done")
        GLOBAL.logger.trace("Loading Fonts")
        GLOBAL.load_fonts()
        GLOBAL.logger.trace("Loading Fonts - Done")

    def implement_menu(self):
        button_start = TextButton(position=(20, 10),
                                  dimension=(200, 0),
                                  grow_height_with_text=True,
                                  grow_width_with_text=True,
                                  text="Start",
                                  callback_function=self.start,
                                  style_dict={"text_align_x": "CENTER",
                                              "text_align_y": "CENTER"})
        button_load = TextButton(position=(50, 80),
                                 dimension=(200, 0),
                                 grow_height_with_text=True,
                                 grow_width_with_text=True, text="Load",
                                 callback_function=self.load,
                                 style_dict={"text_align_x": "CENTER",
                                             "text_align_y": "CENTER"})
        button_quit = TextButton(position=(10, 160),
                                 dimension=(200, 0),
                                 grow_height_with_text=True,
                                 grow_width_with_text=True,
                                 text="Quit",
                                 callback_function=Launcher.quit,
                                 style_dict={"text_align_x": "CENTER",
                                             "text_align_y": "CENTER"})
        line = LineAlignedContainer(int(pg.display.get_surface().get_rect().width / 2),
                                    alignment=LineAlignedContainer.VERTICAL_CENTER,
                                    widgets=(button_start, button_load, button_quit),
                                    space=100)
        self.widgets = line.widgets_as_list()

    def draw(self):
        # Erase All
        screen = pg.display.get_surface()
        screen.fill((0, 0, 0, 0))

        for widget in self.widgets:
            widget.draw(screen)

        pg.display.flip()

    def update(self):
        for widget in self.widgets:
            widget.update()

    def events(self):
        for event in pg.event.get():
            if event.type == pg.QUIT:
                Launcher.quit()
            elif event.type == pg.VIDEORESIZE:
                pg.display.set_mode((event.w, event.h), pg.RESIZABLE)
                line = LineAlignedContainer(int(pg.display.get_surface().get_rect().width / 2),
                                            alignment=LineAlignedContainer.VERTICAL_CENTER,
                                            widgets=self.widgets,
                                            space=100)
                line.move(0, int((event.h - line.rect.height) / 2) - line.rect.top)
            else:
                handled = False
                for widget in self.widgets:
                    if not handled:
                        handled = widget.handle_event(event)

    def run(self):
        while self.launcher_running:
            self.events()
            self.update()
            self.draw()

    def start(self):
        GLOBAL.game = Game()
        GLOBAL.game.post_init()
        GLOBAL.game.new()
        GLOBAL.game.start()

    def load(self):
        self.launcher_running = False
        with open("savegame", "rb") as f:
            GLOBAL.game = pick.load(f)[0]
            GLOBAL.game.reinit_graphics_after_save()

        # Done: starting the game
        GLOBAL.game.start()

    @staticmethod
    def quit():
        pg.quit()
        sys.exit()


if __name__ == '__main__':
    Launcher().run()
