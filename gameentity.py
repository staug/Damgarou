from pygame.sprite import Sprite
from pygame import Surface
from shared import GLOBAL
from default import *

"""
Generic Game entity, which may be displayed on the map (town, player, trap, object...)
Most of the object base code will go there
"""


class GameEntity(Sprite):

    def __init__(self, pos=None, image_ref=None, z_level=2):
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

    def assign_entity_to_region_spritegroup(self, region):
        self.add(region.all_groups[self.z_level])
        # Just in case the position has changed since the original place
        self._reposition_rect()

    def remove_entity_from_region_spritegroup(self, region):
        self.remove(map.all_groups[self.z_level])