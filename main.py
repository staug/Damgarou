import random
import sys

import dill as pick
import pygame as pg

import default
from entity.player import Player
from entity.town import Entrance, Bank, GuildFighter, GuildMule, Shop, Tavern, Trade, Townhall, Temple
from gui import guiwidget
from gui.guiwidget import TextButton, MouseWidget, Label, Style, ImageButton
from gui.guicontainer import LineAlignedContainer
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

        name = None
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

        # Post init on screens
        for screen_name in self.screens:
            self.screens[screen_name].post_init()

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
        Style.set_style()
        button_start = TextButton(position=(20, 10), dimension=(100, 0), grow_height_with_text=True, grow_width_with_text=True, text="Start", callback_function=self.start, style_dict={"text_align_x": "CENTER", "text_align_y": "CENTER"})
        button_load = TextButton(position=(50, 80), dimension=(100, 0), grow_height_with_text=True, grow_width_with_text=True, text="Load", callback_function=self.load, style_dict={"text_align_x": "CENTER", "text_align_y": "CENTER"})
        button_quit = TextButton(position=(10, 160), dimension=(100, 0), grow_height_with_text=True, grow_width_with_text=True, text="Quit", callback_function=Launcher.quit, style_dict={"text_align_x": "CENTER", "text_align_y": "CENTER"})
        line = LineAlignedContainer(int(pg.display.get_surface().get_rect().width / 2),
                                    alignment=LineAlignedContainer.VERTICAL_CENTER,
                                    widgets=(button_start, button_load, button_quit), space=50)
        line.move(0, int((pg.display.get_surface().get_rect().height - line.rect.height) / 2))
        self.widgets = line.widgets_as_list()
        self.widgets.append(Label(text="First new one and this is a very very long one that goes on forever and never quits. Maybe we want to make it scrollable?",
                                  dimension=(200, 80),
                                  position=(30, 220),
                                  grow_width_with_text=False,
                                  grow_height_with_text=True,
                                  multiline=True,
                                  scrollable=True,
                                  style_dict={"bg_color": (255, 0, 0), "text_align_x": "CENTER", "text_align_y": "TOP"}))
        self.widgets.append(ImageButton(callback_function=lambda: print("yo"), image=GLOBAL.img("CURSOR_SWORD_SILVER"), image_hover=GLOBAL.img("CURSOR_SWORD_GOLD"), position=(10, 10)))
        self.widgets.append(MouseWidget(GLOBAL.img("CURSOR_GAUNTLET_BLUE"), MouseWidget.TOP_LEFT))

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
                pg.display.set_mode((event.w, event.h),pg.RESIZABLE)
            else:
                handled = False
                for widget in self.widgets:
                    if not handled:
                        handled = widget.handle_event(event)

    def run(self):
        self.implement_menu()
        while self.launcher_running:
            self.events()
            self.update()
            self.draw()

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
        GLOBAL.game.start()

    @staticmethod
    def quit():
        pg.quit()
        sys.exit()


if __name__ == '__main__':
    Launcher().run()
