import pygame as pg
from shared import GLOBAL
from default import *

class Screen:

    def events(self):
        pass

    def update(self):
        pass

    def draw(self):
        pass

class PlayingScreen(Screen):

    class Camera:
        def __init__(self):
            width_map, height_map = 10, 10  # Will be updated later in the update function, as this depends from current map
            self.camera = pg.Rect(0, 0, width_map, height_map)
            self.width = width_map
            self.height = height_map

        def apply(self, entity):
            return entity.rect.move(self.camera.topleft)

        def apply_rect(self, rect):
            return rect.move(self.camera.topleft)

        def update(self, pos_tile):
            self.width = GLOBAL.game.current_map.background.get_width()
            self.height = GLOBAL.game.current_map.background.get_height()

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

    def __init__(self):
        self.camera = PlayingScreen.Camera()  # this will be updated later
        self.top_playable_position = (32, 64)  # top left corner of the playable screen
        self.pos_player_simu = [0, 0]

    def draw(self):
        # Erase All
        screen = pg.display.get_surface()
        screen.fill(BGCOLOR)

        # Playable Background
        playable_background = pg.Surface((PLAYABLE_WIDTH, PLAYABLE_HEIGHT))
        playable_background.blit(GLOBAL.game.current_map.background,
                                 self.camera.apply_rect(pg.Rect(0,
                                                                0,
                                                                GLOBAL.game.current_map.background.get_width(),
                                                                GLOBAL.game.current_map.background.get_height())))
        # Add all the game objects - To be removed
        psimu_surface = pg.Surface(TILESIZE_SCREEN)
        psimu_surface.fill((255, 166, 151))
        playable_background.blit(psimu_surface, self.camera.apply_rect(pg.Rect(self.pos_player_simu[0] * TILESIZE_SCREEN[0],
                                                                     self.pos_player_simu[1] * TILESIZE_SCREEN[1],
                                                                     TILESIZE_SCREEN[0],
                                                                     TILESIZE_SCREEN[1]
                                                                     )))

        for sprite_group in GLOBAL.game.current_map.all_groups:
            for entity in sprite_group:
                playable_background.blit(entity.image, self.camera.apply(entity))

        # Playable background commit
        screen.blit(playable_background, pg.Rect(self.top_playable_position, (PLAYABLE_WIDTH, PLAYABLE_HEIGHT)))
        pg.display.flip()

    def update(self):
        self.camera.update(self.pos_player_simu)

    def events(self):
        # TODO Update all the keys, and change player simu
        for event in pg.event.get():
            if event.type == pg.QUIT:
                GLOBAL.game.quit()
            if event.type == pg.KEYDOWN:
                if event.key in (pg.K_LEFT, pg.K_q, pg.K_KP4):
                    self.pos_player_simu[0] -= 1
                if event.key in (pg.K_RIGHT, pg.K_d, pg.K_KP6):
                    self.pos_player_simu[0] += 1
                if event.key in (pg.K_UP, pg.K_z, pg.K_KP8):
                    self.pos_player_simu[1] -= 1
                if event.key in (pg.K_DOWN, pg.K_x, pg.K_KP2):
                    self.pos_player_simu[1] += 1

            if event.type == pg.MOUSEBUTTONDOWN:
                (button1, button2, button3) = pg.mouse.get_pressed()
                (x, y) = pg.mouse.get_pos()
                x -= self.top_playable_position[0]
                y -= self.top_playable_position[1]
                if button1:
                    (rev_x, rev_y) = self.camera.reverse((x, y))
                    (x, y) = (int(rev_x / TILESIZE_SCREEN[0]), int(rev_y / TILESIZE_SCREEN[1]))

                    print(GLOBAL.game.current_map.tiles[x][y].tile_type)

