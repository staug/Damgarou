import dill as pick
import pygame as pg
import sys

from default import *
from gui.guiwidget import Widget, ProgressBar, Style, SimpleLabel, RadioButtonGroup, SelectButton
from shared import GLOBAL
from utilities import FieldOfView


class Screen:

    def __init__(self):
        self.widgets = []

    def events(self):
        pass

    def update(self):
        pass

    def draw(self):
        pass

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

    def draw(self):
        # Erase All
        screen = pg.display.get_surface()
        screen.fill(BGCOLOR)

        for widget in self.widgets:
            widget.draw(screen)

        pg.display.flip()

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

    def __init__(self, playershell):
        Screen.__init__(self)
        self.player_running = True
        self.playershell = playershell
        self.run()

    def build_widgets(self):
        Style.set_style()
        label_gender = SimpleLabel(text="Gender")
        genderchoice = RadioButtonGroup(texts=("Male", "Female", "Other"),
                                        position=(0,50),
                                        callback_function=self.gender_chosen,
                                        icon_image_not_selected=GLOBAL.img("ICON_CHECK_BEIGE"),
                                        icon_image_selected=GLOBAL.img("ICON_CIRCLE_BLUE"))

        label_race = SelectButton(texts=["Race1", "Race2        "], callback_function=self.gender_chosen, position=(0,200))

        self.widgets.append(label_gender)
        self.widgets.append(genderchoice)
        self.widgets.append(label_race)

    def draw(self):
        # Erase All
        screen = pg.display.get_surface()
        screen.fill(BGCOLOR)

        for widget in self.widgets:
            widget.draw(screen)

        pg.display.flip()

    def update(self):
        for widget in self.widgets:
            widget.update()

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

    def run(self):
        self.build_widgets()
        while self.player_running:
            self.events()
            self.update()
            self.draw()

    def gender_chosen(self, *args, **kwargs):
        print("yes" + str(args) +"--"+str(kwargs))


def test(fighter):
    print("YO" + fighter.name)
