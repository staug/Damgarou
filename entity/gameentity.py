from pygame.sprite import Sprite
from pygame import Surface
import pygame as pg
from math import sqrt
from shared import GLOBAL
from default import *
import random as rd

"""
Generic Game entity, which may be displayed on the map (town, player, trap, object...)
Most of the object base code will go there
"""


class GameEntity(Sprite):

    COUNTER = 0

    def __init__(self,
                 name=None,
                 pos=None,
                 image_ref=None,
                 z_level=2,
                 blocking_tile_list=None,
                 blocking_view_list=None,
                 vision=1,
                 blocks=False,
                 actionable=None,
                 ai=None):

        Sprite.__init__(self)
        if not pos:
            pos = (-1, -1)
        (self.x, self.y) = pos

        self.name = name
        if name is None:
            GameEntity.COUNTER += 1
            self.name = "Entity ".format(GameEntity.COUNTER)

        # Image settings
        self.z_level = z_level  # The depth. Default is 2, min is 0.
        self.image_ref = image_ref
        self.image = None
        self.animated = False
        self.current_region_name = None
        self.current_region = None
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

        self.ai = ai
        if self.ai:
            self.ai.owner = self

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

    def update_graphics(self, new_image_ref):
        """
        Update the graphical reference, and force a reset of the graphical function
        :param new_image_ref: the new image reference
        :return: nothing
        """
        self.image_ref = new_image_ref
        self.init_graphics()

    def clean_before_save(self, image_only=False):
        """
        Clean all graphical objects, remove from sprite dictionary and remove the game reference
        :return:
        """
        self.image = None
        self.animated = False
        if hasattr(self, "dict_image"):
            # self.dict_image = None
            delattr(self, "dict_image")
        if hasattr(self, "list_image"):
            self.list_image = None
            delattr(self, "list_image")

    def _reposition_rect(self):
        self.rect = self.image.get_rect()
        self.rect.centerx = self.x * TILESIZE_SCREEN[0] + int(TILESIZE_SCREEN[1] / 2)  # initial position for the camera
        self.rect.centery = self.y * TILESIZE_SCREEN[0] + int(TILESIZE_SCREEN[1] / 2)

    def assign_entity_to_region(self, region):
        self.add(region.all_groups[self.z_level])
        self.current_region_name = region.name
        self.current_region = region
        region.region_entities.add(self)
        if self.ai is not None:
            region.ticker.schedule_turn(self.ai.speed, self.ai)

    def remove_entity_from_region(self, region):
        self.remove(region.all_groups[self.z_level])
        self.current_region_name = None
        self.current_region = None
        region.region_entities.remove(self)
        region.ticker.unregister(self.ai)

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

    def move(self, dx=0, dy=0, with_fight=False):
        """
        Try to move the entity.
        Return True if an action was done (either move or attack)
        """

        # Test if we enter the actionable zone of an entity
        for entity in GLOBAL.game.current_region.region_entities:
            if entity != self and entity.actionable is not None and \
                            (self.x + dx, self.y + dy) in entity.actionable.action_field:
                self.x += dx
                self.y += dy
                ok_to_move = entity.actionable.action(self)
                self.x -= dx
                self.y -= dy
                if entity.blocks:
                    if ok_to_move is not None and not ok_to_move:
                        # We triggered an object, and it prevented the move (like a door not opening)
                        return False

        # Test if we collide with an other enemy, then we enter in a fight mode
        #TODO implement fight
        if with_fight:
            assert True, "FIGHT NOT IMPLEMENTED YET"

        # Test if we collide with the terrain, and terrain only
        destination_tile = GLOBAL.game.current_region.tiles[self.x + dx][self.y + dy]
        if not destination_tile.block_for(self):
            # now test the list of objects
            for entity in GLOBAL.game.current_region.region_entities:
                if entity != self and entity.blocks and entity.x == self.x + dx and entity.y == self.y + dy:
                    return False
            # success
            self.x += dx
            self.y += dy
            if self.animated and (dx != 0 or dy != 0):
                self.last_direction = (dx, dy)

            GLOBAL.game.invalidate_fog_of_war = True
            # self.game.ticker.ticks_to_advance += self.speed_cost_for(c.AC_ENV_MOVE)
            return True

        return False


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


class AIEntity:

    def __init__(self, speed=1):
        self.owner = None
        self.speed = speed  # the speed represents the time between two turns

    def move_towards_position(self, pos, with_fight=False):
        # vector from this object to the target, and distance
        dx = pos[0] - self.owner.x
        dy = pos[1] - self.owner.y
        distance = sqrt(dx ** 2 + dy ** 2)

        # normalize it to length 1 (preserving direction), then round it and
        # convert to integer so the movement is restricted to the map grid
        if distance != 0:
            dx = int(round(dx / distance))
            dy = int(round(dy / distance))
        else:
            dx = dy = 0
        return self.owner.move(dx, dy, with_fight=with_fight)

    def move_towards_entity(self, other_entity, with_fight=False):
        self.move_towards_position(other_entity.pos, with_fight=with_fight)

    def move_randomly(self, with_fight=False):
        """
        Move by 1 around the current position. The destination should be non blocking.
        If no tiles match, then no move is taken.
        :return:
        """
        delta = [(-1, -1), (-1, 0), (-1, 1), (0, 1), (0, -1), (1, -1), (1, 0), (1, 1)]
        rd.shuffle(delta)
        x, y = self.owner.pos
        while len(delta) > 0:
            dx, dy = delta.pop()
            if self.move_towards_position((x + dx, y + dy), with_fight=with_fight):
                return

    def take_turn(self):
        assert True, "Entity has not redefined the take turn"


class WanderingAIEntity(AIEntity):

    def __init__(self, speed):
        AIEntity.__init__(self, speed=speed)

    def take_turn(self):
        self.move_randomly(with_fight=False)
        print("{} moves to {}".format(self.owner.name, self.owner.pos))
        GLOBAL.game.world[self.owner.current_region_name].ticker.schedule_turn(self.speed, self)
