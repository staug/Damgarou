import pygame as pg
from shared import GLOBAL

class Screen:

    def events(self):
        pass

    def update(self):
        pass

    def draw(self):
        pass

class PlayingScreen(Screen):

    def events(self):
        for event in pg.event.get():
            if event.type == pg.QUIT:
                GLOBAL.game.quit()