import random
import sys

import dill as pick
import pygame as pg

from default import *
from entity.player import Player
from entity.town import Entrance, Bank, GuildFighter, GuildMule, Shop, Tavern, Trade, Townhall, Temple
from gui import guiwidget
from gui.guicontainer import LineAlignedContainer
from gui.guiwidget import Widget, SimpleLabel, \
    RadioButtonGroup, SelectButton, TextInput, TextButton
from region.region import RegionFactory
from shared import GLOBAL
from utilities import FieldOfView
from utilities import MName


class Screen:

    def __init__(self):
        self.widgets = []

    def events(self):
        pass

    def update(self):
        for widget in self.widgets:
            widget.update()


    def draw(self):
        # Erase All
        screen = pg.display.get_surface()
        screen.fill(BGCOLOR)

        for widget in self.widgets:
            widget.draw(screen)

        pg.display.flip()

    def post_init(self):
        """
        This method is called when all entities (including player!) are created
        :return: Nothing
        """
        pass


class PlayingScreen(Screen):
    class Camera:
        def __init__(self):
            width_map, height_map = 10, 10  # Will be updated later in the update function,
            # this depends from current map
            self.camera = pg.Rect(0, 0, width_map, height_map)
            self.width = width_map
            self.height = height_map

        def apply(self, entity):
            return entity.rect.move(self.camera.topleft)

        def apply_rect(self, rect):
            return rect.move(self.camera.topleft)

        def update(self, pos_tile):
            self.width = GLOBAL.game.current_region.background.get_width()
            self.height = GLOBAL.game.current_region.background.get_height()

            x = -pos_tile[0] * TILESIZE_SCREEN[0] + int(PLAYABLE_WIDTH / 2)
            y = -pos_tile[1] * TILESIZE_SCREEN[1] + int(PLAYABLE_HEIGHT / 2)

            # limit scrolling to map size
            x = min(0, x)  # left
            y = min(0, y)  # up
            x = max(-(self.width - PLAYABLE_WIDTH), x)
            y = max(-(self.height - PLAYABLE_HEIGHT), y)

            # and apply it to the camera rect
            self.camera = pg.Rect(x, y, self.width, self.height)

        def reverse(self, pos):
            """
            Return the pos in the original file from a position on the screen.
            Used for example to get the position following a mouse click
            """
            (screen_x, screen_y) = pos
            (cam_x, cam_y) = self.camera.topleft
            return screen_x - cam_x, screen_y - cam_y

    class PlayableScreen(Widget):
        def __init__(self, top_left):
            self.top_left = top_left
            self.dimension = (PLAYABLE_WIDTH, PLAYABLE_HEIGHT)
            self.camera = PlayingScreen.Camera()
            self.fog_of_war_mask = None

        def update(self):
            for sprite_group in GLOBAL.game.current_region.all_groups:
                for entity in sprite_group:
                    entity.update()
            self.camera.update(GLOBAL.game.player.pos)

        def draw(self, screen):
            # Playable Background
            playable_background = pg.Surface(self.dimension)
            playable_background.blit(GLOBAL.game.current_region.background,
                                     self.camera.apply_rect(pg.Rect(0, 0, PLAYABLE_WIDTH, PLAYABLE_HEIGHT)))

            # Add all the game objects on the playable entity
            for sprite_group in GLOBAL.game.current_region.all_groups:
                for entity in sprite_group:
                    playable_background.blit(entity.image, self.camera.apply(entity))

            # FOW
            if GLOBAL.game.invalidate_fog_of_war or self.fog_of_war_mask is None:
                # Recompute the player vision matrix, that flag the explored part
                FieldOfView.get_vision_matrix_for(GLOBAL.game.player, GLOBAL.game.current_region, flag_explored=True)

                self.fog_of_war_mask = pg.Surface((PLAYABLE_WIDTH, PLAYABLE_HEIGHT), pg.SRCALPHA, 32)

                black = pg.Surface(TILESIZE_SCREEN)
                black.fill(BGCOLOR)
                gray = pg.Surface(TILESIZE_SCREEN, pg.SRCALPHA, 32)
                gray.fill((0, 0, 0, 120))
                for x in range(GLOBAL.game.current_region.tile_width):
                    for y in range(GLOBAL.game.current_region.tile_height):
                        if GLOBAL.game.current_region.tiles[x][y].explored:
                            self.fog_of_war_mask.blit(gray,
                                                      self.camera.apply_rect(
                                                          pg.Rect((x * TILESIZE_SCREEN[0],
                                                                   y * TILESIZE_SCREEN[1]), TILESIZE_SCREEN)))
                        else:
                            self.fog_of_war_mask.blit(black,
                                                      self.camera.apply_rect(
                                                          pg.Rect((x * TILESIZE_SCREEN[0],
                                                                   y * TILESIZE_SCREEN[1]), TILESIZE_SCREEN)))
                GLOBAL.game.invalidate_fog_of_war = False

            playable_background.blit(self.fog_of_war_mask, (0, 0))

            # Playable background commit
            screen.blit(playable_background, pg.Rect(self.top_left, (PLAYABLE_WIDTH, PLAYABLE_HEIGHT)))

        def handle_event(self, event):

            if event.type == pg.KEYDOWN:

                # Movement
                if event.key in (pg.K_LEFT, pg.K_q, pg.K_KP4):
                    GLOBAL.game.player.move(dx=-1)
                    return True
                if event.key in (pg.K_RIGHT, pg.K_d, pg.K_KP6):
                    GLOBAL.game.player.move(dx=1)
                    return True
                if event.key in (pg.K_UP, pg.K_z, pg.K_KP8):
                    GLOBAL.game.player.move(dy=-1)
                    return True
                if event.key in (pg.K_DOWN, pg.K_x, pg.K_KP2):
                    GLOBAL.game.player.move(dy=1)
                    return True

                # Save
                if event.key == pg.K_s:
                    print("SAVING and EXIT")
                    GLOBAL.game.clean_graphics_before_save()
                    GLOBAL.clean_before_save()
                    self.fog_of_war_mask = None

                    with open("savegame", "wb") as f:
                        pick.dump([GLOBAL.game], f)
                    GLOBAL.game.quit()

            if event.type == pg.MOUSEBUTTONDOWN:
                (button1, button2, button3) = pg.mouse.get_pressed()
                (x, y) = pg.mouse.get_pos()
                if not pg.Rect(self.top_left, (PLAYABLE_WIDTH, PLAYABLE_HEIGHT)).collidepoint(x, y):
                    return False
                if button1:
                    (rev_x, rev_y) = self.camera.reverse((x - self.top_left[0], y - self.top_left[1]))
                    (x, y) = (int(rev_x / TILESIZE_SCREEN[0]), int(rev_y / TILESIZE_SCREEN[1]))
                    print(GLOBAL.game.current_region.tiles[x][y].tile_type)
                    return True
            return False

    def __init__(self):
        Screen.__init__(self)
        self.widgets.append(PlayingScreen.PlayableScreen((10, 10)))

    def post_init(self):
        pass
        '''self.widgets.append(ProgressBar(
            position=(10, 10),
            dimension=(100, 10),
            object_to_follow=GLOBAL.game.player,
            attribute_to_follow="test_attribute",
            max_value=100,
            with_text=True,
            style_dict={
                "color": (255, 0, 0),
                "bg_color": (0, 0, 255),
                "rounded": True,
                "theme": Style.THEME_DARK_BROWN
            }
        ))'''

    def update(self):
        # Update region
        GLOBAL.game.current_region.ticker.advance_ticks()

        for widget in self.widgets:
            widget.update()

    def events(self):
        for event in pg.event.get():
            if event.type == pg.QUIT:
                GLOBAL.game.quit()
            else:
                handled = False
                for widget in self.widgets:
                    if not handled:
                        handled = widget.handle_event(event)


class PlayerCreationScreen(Screen):

    def __init__(self):
        Screen.__init__(self)
        self.name = MName.person_name()
        self.playershell = {}

        self.label_strength_value = None
        self.label_charisma_value = None
        self.label_friendship_value = None
        self.label_erudition_value = None

        self.build_widgets()

    def build_widgets(self):
        label_gender = SimpleLabel(text="Gender:")
        genderchoice = RadioButtonGroup(texts=("Male", "Female", "Other"),
                                        callback_function=self.gender_chosen,
                                        icon_image_not_selected=GLOBAL.img("ICON_CHECK_BLUE"),
                                        icon_image_selected=GLOBAL.img("ICON_CHECK_BEIGE"),
                                        orientation=RadioButtonGroup.HORIZONTAL)
        self.playershell["Gender"] = "Male"

        label_race = SimpleLabel(text="Race:")
        racechoice = SelectButton(texts=["Human", "Dwarf", "Elf", "Hobbit"],
                                  callback_function=self.race_chosen)
        self.playershell["Race"] = "Race1"

        label_characteristics = SimpleLabel(text="Characteristics")
        label_strength = SimpleLabel(text="Strength")
        label_charisma = SimpleLabel(text="Charisma")
        label_friendship = SimpleLabel(text="Friendship")
        label_erudition = SimpleLabel(text="Erudition")
        self.label_strength_value = SimpleLabel(text="99")
        self.label_charisma_value = SimpleLabel(text="99")
        self.label_friendship_value = SimpleLabel(text="99")
        self.label_erudition_value = SimpleLabel(text="99")

        reroll = TextButton(callback_function=self.reroll_chosen, text="Reroll",
                            dimension=(pg.display.get_surface().get_rect().width - 200, 10),
                            style_dict={"text_align_x":"CENTER"})

        nameinput= TextInput(max_displayed_input=30, property_to_follow=self.name,
                             callback_function=self.validate, style_dict={"text":"Let's go!"})

        # First we align all widgets vertically
        LineAlignedContainer((50, 100), end_position=(50, pg.display.get_surface().get_rect().height - 100),
                             alignment=LineAlignedContainer.VERTICAL_LEFT, auto_space=True,
                             widgets=(label_gender,
                                      label_race,
                                      label_characteristics,
                                      label_strength,
                                      label_charisma,
                                      label_friendship,
                                      label_erudition,
                                      reroll,
                                      nameinput))

        # Now the lines (note we don't care about the y position on the end position)
        LineAlignedContainer(label_gender.rect.topleft, widgets=(label_gender, genderchoice),
                             alignment=LineAlignedContainer.HORIZONTAL_TOP,
                             end_position=(pg.display.get_surface().get_rect().width - 50, 0), auto_space=True)
        LineAlignedContainer(label_race.rect.topleft, widgets=(label_race, racechoice),
                             alignment=LineAlignedContainer.HORIZONTAL_TOP,
                             end_position=(pg.display.get_surface().get_rect().width - 50, 0), auto_space=True)
        LineAlignedContainer(label_strength.rect.topleft, widgets=(label_strength, self.label_strength_value),
                             alignment=LineAlignedContainer.HORIZONTAL_TOP,
                             end_position=(pg.display.get_surface().get_rect().width - 50, 0), auto_space=True)
        LineAlignedContainer(label_charisma.rect.topleft, widgets=(label_charisma, self.label_charisma_value),
                             alignment=LineAlignedContainer.HORIZONTAL_TOP,
                             end_position=(pg.display.get_surface().get_rect().width - 50, 0), auto_space=True)
        LineAlignedContainer(label_friendship.rect.topleft, widgets=(label_friendship, self.label_friendship_value),
                             alignment=LineAlignedContainer.HORIZONTAL_TOP,
                             end_position=(pg.display.get_surface().get_rect().width - 50, 0), auto_space=True)
        LineAlignedContainer(label_erudition.rect.topleft, widgets=(label_erudition, self.label_erudition_value),
                             alignment=LineAlignedContainer.HORIZONTAL_TOP,
                             end_position=(pg.display.get_surface().get_rect().width - 50, 0), auto_space=True)
        # Last let's align the characteristics vertically for better effect
        LineAlignedContainer(self.label_strength_value.rect.topright,
                             alignment=LineAlignedContainer.VERTICAL_RIGHT,
                             widgets=(self.label_strength_value, self.label_charisma_value,
                                      self.label_friendship_value, self.label_erudition_value))

        for w in (label_gender, genderchoice, label_race, racechoice,
                  label_characteristics,
                  label_strength, label_charisma, label_friendship, label_erudition,
                  self.label_strength_value, self.label_charisma_value,
                  self.label_friendship_value, self.label_erudition_value,
                  reroll, nameinput
                  ):
            self.widgets.append(w)

        self.reroll_chosen()

    def events(self):
        for event in pg.event.get():
            if event.type == pg.QUIT:
                if GLOBAL.game:
                    GLOBAL.game.quit()
                else:
                    pg.quit()
                    sys.exit()
            else:
                handled = False
                for widget in self.widgets:
                    if not handled:
                        handled = widget.handle_event(event)

    def gender_chosen(self, *args, **kwargs):
        self.playershell["Gender"] = str(args[0])
        print(self.playershell)

    def race_chosen(self, *args, **kwargs):
        self.playershell["Race"] = str(args[0])
        print(self.playershell)

    def reroll_chosen(self, *args, **kwargs):

        self.playershell["Strength"] = random.randint(10,20)
        self.playershell["Charisma"] = random.randint(10,20)
        self.playershell["Friendship"] = random.randint(10,20)
        self.playershell["Erudition"] = random.randint(10,20)

        self.label_strength_value.set_text(str(self.playershell["Strength"]), recreate_background=False)
        self.label_charisma_value.set_text(str(self.playershell["Charisma"]), recreate_background=False)
        self.label_erudition_value.set_text(str(self.playershell["Erudition"]), recreate_background=False)
        self.label_friendship_value.set_text(str(self.playershell["Friendship"]), recreate_background=False)

    def validate(self, *args, **kwargs):
        self.playershell["Name"] = str(args[0])
        print(self.playershell)
        GLOBAL.game.player = Player(player_dict=self.playershell)
        GLOBAL.game.update_state(GLOBAL.game.GAME_STATE_WORLD_CREATION)

class WorldCreationScreen(Screen):

    def __init__(self):
        Screen.__init__(self)

    def update(self):

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
                                                                  # Bank(),
                                                                  # GuildMule(),
                                                                  GuildFighter(),
                                                                  # Shop(),
                                                                  # Tavern(), Trade(), Townhall(), Temple()
                                                                  )
                                                   )
                town_list.append(town_region)
                GLOBAL.game.world[name_town] = town_region

            GLOBAL.game.world[name] = RegionFactory.invoke(name,
                                                    region_type=RegionFactory.REGION_WILDERNESS,
                                                    town_list=town_list)
            player_spawn_pos = town_list[0].town.pos  # small hack

        guiwidget.display_single_message_on_screen("World ok")

        GLOBAL.game.current_region = GLOBAL.game.world[name]
        # We start the player, and we add it at his spawning position (a town of hte latest wilderness)
        #self.player = Player()
        GLOBAL.game.player.assign_entity_to_region(GLOBAL.game.current_region)
        (GLOBAL.game.player.x, GLOBAL.game.player.y) = player_spawn_pos
        GLOBAL.game.update_state(GLOBAL.game.GAME_STATE_PLAYING)


## ACTIONS FOR WIDGETS

def enroll_fighter(fighter, buildingscreen):
    print(fighter.name + " joined the player")
    GLOBAL.game.player.add_fighter(fighter)  # this removes from the world
    buildingscreen.building.fighter_list.remove(fighter)  # we remove the fighter from eth building as well
    buildingscreen.attach_building(
        buildingscreen.building)  #   and ask to redraw the widgets (seem there is a pb for the  last  fighter)
