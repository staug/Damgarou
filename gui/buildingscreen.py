import os

import pygame as pg

from default import BGCOLOR, FONT_FOLDER, FONT_NAME, WHITE
from gui.guicontainer import LineAlignedContainer
from gui.guiwidget import TextButton
from gui.screen import Screen, enroll_fighter
from shared import GLOBAL


class BuildingScreen(Screen):
    """
    This set of screens is to represent the action inside a building.
    Pressing Escape will go back to the regular state.
    """

    def __init__(self):
        Screen.__init__(self)
        self.building = None

    def attach_building(self, building):
        self.building = building
        self.widgets = []

        if self.building.is_guild_fighter() and len(self.building.fighter_list) > 0:
            for fighter in self.building.fighter_list:
                button = TextButton(text=fighter.name,
                                    callback_function=lambda myfighter=fighter, buildingscreen=self: enroll_fighter(
                                        myfighter, buildingscreen),
                                    grow_width_with_text=True,
                                    grow_height_with_text=True)
                self.widgets.append(button)

            line = LineAlignedContainer(int(pg.display.get_surface().get_rect().width / 2),
                                        alignment=LineAlignedContainer.VERTICAL_CENTER,
                                        widgets=self.widgets, space=50)
            line.move(0, int((pg.display.get_surface().get_rect().height - line.rect.height) / 2))

    def draw(self):
        # Erase All
        screen = pg.display.get_surface()
        screen.fill(BGCOLOR)

        if len(self.widgets) == 0:
            font = pg.font.Font(os.path.join(FONT_FOLDER, FONT_NAME), 20)
            text = font.render("Building " + self.building.name, True, WHITE)
            text_rect = text.get_rect()

            left_x = screen.get_rect().centerx - int(text_rect.width / 2)
            top_y = screen.get_rect().centery - int(text_rect.height / 2)
            screen.blit(text, (left_x, top_y))
        else:
            for widget in self.widgets:
                widget.draw(screen)

        pg.display.flip()

    def update(self):
        for widget in self.widgets:
            widget.update()

    def events(self):
        for event in pg.event.get():
            if event.type == pg.QUIT:
                GLOBAL.game.quit()
            elif event.type == pg.KEYDOWN and event.key == pg.K_ESCAPE:
                self.building = None
                self.widgets = []
                GLOBAL.game.update_state(GLOBAL.game.GAME_STATE_PLAYING)
            else:
                handled = False
                for widget in self.widgets:
                    if not handled:
                        handled = widget.handle_event(event)
