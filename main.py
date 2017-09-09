import pygame as pg
import thorpy
import sys
import os
import default
import guiwidget

from shared import GLOBAL
from tilemap import MapFactory


class Game:

    GAME_STATE_PLAYING = 'Playing'
    GAME_STATE_INVENTORY = 'Inventory'
    GAME_STATE_MAP = 'Map'
    GAME_STATE_CHARACTER = 'Character'

    def __init__(self):

        self.game_state = Game.GAME_STATE_PLAYING
        self.player_took_action = False
        self.minimap_enabled = False
        self.game_running = True

    def new(self):
        self.objects = []
        self.level = 1

        #self.map = DungeonMapFactory("MerchantRogue Caves - Level {}".format(self.level)).map
        guiwidget.display_single_message_on_screen("Building level")
        MapFactory("MerchantRogue Caves - Level {}".format(self.level))
        guiwidget.display_single_message_on_screen("Level ok")

        #self.minimap = Minimap(self)

    def start(self):
        self.run()

    def run(self):
        while self.game_running:
            for event in pg.event.get():
                if event.type == pg.QUIT:
                    Game.quit()

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
        self.init_pygame_subsystem()
        self.load_data()
        self.launcher_running = True

    def init_pygame_subsystem(self):
        GLOBAL.logger.trace("Initializing Pygame")
        pg.display.init()
        pg.font.init()
        pg.display.set_mode((800, 600), pg.RESIZABLE)
        pg.display.set_caption(default.GAME_TITLE + "-" + default.GAME_VER)
        thorpy.set_theme("human")
        GLOBAL.logger.trace("Initializing Pygame - Done")

    def load_data(self):
        GLOBAL.logger.trace("Loading Images")
        GLOBAL.load_images()
        GLOBAL.logger.trace("Loading Images - Done")

    def implement_menu(self):

        font = pg.font.Font(os.path.join(default.FONT_FOLDER, default.FONT_NAME), 18)

        button_start = thorpy.make_button("Start", func=self.start)
        button_start.set_size((100, None))
        button_start.set_font(font)
        button_start.set_font_size(16)

        button_load = thorpy.make_button("Load")
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

    @staticmethod
    def quit():
        pg.quit()
        sys.exit()

if __name__ == '__main__':
    Launcher().run()
