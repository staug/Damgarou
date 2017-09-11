from pygame.sprite import Sprite
from pygame import Surface
import pygame as pg
from shared import GLOBAL
from default import *

"""
Generic Game entity, which may be displayed on the map (town, player, trap, object...)
Most of the object base code will go there
"""


class GameEntity(Sprite):

    def __init__(self,
                 pos=None,
                 image_ref=None,
                 z_level=2,
                 blocking_tile_list=None,
                 blocking_view_list=None,
                 vision=1,
                 blocks=False,
                 actionable=None):

        Sprite.__init__(self)
        if not pos:
            pos = (-1, -1)
        (self.x, self.y) = pos

        # Image settings
        self.z_level = z_level  # The depth. Default is 2, min is 0.
        self.image_ref = image_ref
        self.image = None
        self.animated = False
        self.init_graphics()

        # Blocking: what the object can go over, what it can see over, and if the object prevents movement upon itself
        self.blocking_tile_list = blocking_tile_list
        self.blocking_view_list = blocking_view_list
        self.blocks = blocks
        self.base_vision_radius = vision

        # Components
        self.actionable = actionable
        if self.actionable:
            self.actionable.owner = self

    @property
    def pos(self):
        return self.x, self.y

    # GRAPHICAL RELATED FUNCTIONS
    def init_graphics(self):
        """
        Initiate all graphical objects
        :return: Nothing
        """
        if type(self.image_ref) is Surface:
            # This is the case for the special visual effect
            self.image = self.image_ref
        else:
            image = GLOBAL.img(self.image_ref)
            if type(image) is tuple:
                # for decode purpose
                self.image = Surface(TILESIZE_SCREEN)
                self.image.fill(image)
            elif type(image) is list or type(image) is dict:
                self.animated = True
                self.current_frame = 0
                self.last_update = 0
                if type(image) is list:
                    self.list_image = image
                    self.image = self.list_image[self.current_frame]
                else:
                    self.last_direction = (1, 0)
                    self.dict_image = image
                    self.image = self.dict_image['E'][self.current_frame]
            else:
                self.image = image
        self._reposition_rect()

    def _reposition_rect(self):
        self.rect = self.image.get_rect()
        self.rect.centerx = self.x * TILESIZE_SCREEN[0] + int(TILESIZE_SCREEN[1] / 2)  # initial position for the camera
        self.rect.centery = self.y * TILESIZE_SCREEN[0] + int(TILESIZE_SCREEN[1] / 2)

    def assign_entity_to_region(self, region):
        self.add(region.all_groups[self.z_level])
        region.region_entities.add(self)

    def remove_entity_from_region(self, region):
        self.remove(map.all_groups[self.z_level])
        region.region_entities.remove(self)

    def animate(self):
        now = pg.time.get_ticks()
        delta = 200
        if hasattr(self, "ai") and self.ai is not None:
            if hasattr(self.ai, "speed"):
                delta = self.ai.speed * 30
        elif hasattr(self, "speed"):
            delta = self.speed * 30
        if now - self.last_update > delta:
            self.last_update = now
            reference = 'E'
            if hasattr(self, "dict_image"):
                if self.last_direction[0] < 0:
                    reference = 'W'
                if self.last_direction[0] > 0:
                    reference = 'E'
                if self.last_direction[1] < 0:
                    reference = 'N'
                if self.last_direction[1] > 0:
                    reference = 'S'
                if "NW" in self.dict_image:
                    if self.last_direction == (-1, -1):
                        reference = "NW"
                    elif self.last_direction == (1, 1):
                        reference = "SE"
                    elif self.last_direction == (-1, 1):
                        reference = "SW"
                    elif self.last_direction == (1, -1):
                        reference = "NE"
                self.current_frame = (self.current_frame + 1) % len(self.dict_image[reference])
                self.image = self.dict_image[reference][self.current_frame]
            else:
                self.current_frame = (self.current_frame + 1) % len(self.list_image)
                self.image = self.list_image[self.current_frame]

    def update(self):
        if self.animated:
            self.animate()
        self._reposition_rect()



class ActionableEntity:
    """
    An actionable entity is an object which is triggered when something (player, monster...) is around (or directly in).
    This is typically a door, a trap, a town...
    """
    def __init__(self, radius=0, actionable_by_player_only=True, function=None):
        self.radius = radius  # the radius for triggering the function
        self.owner = None
        self.actionable_by_player_only = actionable_by_player_only
        self._action_field = None
        self.function = function

    @property
    def action_field(self):
        if self._action_field is not None:
            return self._action_field
        else:
            if self.owner is not None:
                self._action_field = [self.owner.pos]
                for i in range(-self.radius, self.radius):
                    if (self.owner.pos[0] + i, self.owner.pos[1]) not in self._action_field:
                        self._action_field.append((self.owner.pos[0] + i, self.owner.pos[1]))
                    if (self.owner.pos[0], self.owner.pos[1] + i) not in self._action_field:
                        self._action_field.append((self.owner.pos[0], self.owner.pos[1] + i))
                return self._action_field
            else:
                return []

    def action(self, entity_that_actioned):
        if self.function is None:
            print("No function created")
        else:
            if self.actionable_by_player_only:
                if entity_that_actioned == GLOBAL.game.player:
                    return self.function(self.owner, entity_that_actioned)
            else:
                return self.function(self.owner, entity_that_actioned)