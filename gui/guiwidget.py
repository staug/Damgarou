import pygame as pg
import os
import default
import random
from shared import GLOBAL
from copy import deepcopy


class Widget:

    def __init__(self):
        self.position = (0, 0)
        self.rect = None
        self.image = None

    def update(self):
        """
        In general this method is not really usefull, but it is called from the master.
        Can be used to prepare the image
        :return: 
        """
        pass

    def handle_event(self, event):
        """
        Called to handle event - return True if the event has been processed, False otherwise
        :param event: a Pygame Event
        :return: True if the event has been processed, false otherwise
        """
        pass

    def draw(self, screen):
        """
        Default implementation: blit the premade image on the screen surface. Assumes that a rect has been created.
        :param screen: the surface to blit on.
        :return: 
        """
        assert self.image, "Image doesn't exist so can't blit"
        assert self.rect, "Rect doesn't exist so can't blit"
        screen.blit(self.image, self.rect)


class ProgressBar(Widget):
    # TODO Refactor according to widget standards & using teh rounded surface with radius = 1
    """
    A progress bar widget. Tracks the value of an object.
    """
    PROGRESSBAR_FONT = 'freesansbold.ttf'

    def __init__(self,
                 position,
                 dimension,
                 object_to_follow,
                 attribute_to_follow,
                 max_value,
                 bar_color,
                 back_color=(0, 0, 0, 0),
                 font=None,
                 with_text=True):
        """
        Define a progress bar
        :param position: (x, y) on the screen
        :param dimension: (width, height) of the progress bar
        :param object_to_follow: the object to follow, linked to the attribute
        :param attribute_to_follow: the attribute to follow
        :param max_value: the maximum value the attribute can take
        :param bar_color: (r, g, b) the color of the external part and of the filled part
        :param back_color: (r, g, b, a) the color of the background when the bar is not filled. Default is transparent.
        :param font: the font to print in case of text
        :param with_text: display a text on the bar
        """

        self._position = position
        self._dimension = dimension

        assert hasattr(object_to_follow, attribute_to_follow), \
            "Progressbar: The object {} doesn't have an attribute {} that can be followed".format(object_to_follow,
                                                                                                  attribute_to_follow)
        self._object_to_follow = object_to_follow
        self._attribute_to_follow = attribute_to_follow

        self._max_value = max_value
        self._bar_color = bar_color
        self._back_color = back_color

        self._current_value = getattr(object_to_follow, attribute_to_follow)
        self._need_redraw = True

        if font is None:
            self._font = pg.font.Font(ProgressBar.PROGRESSBAR_FONT, 14)
        else:
            self._font = font
        self._with_text = with_text

    def handle_event(self, event):
        pass

    def change_target(self, object_to_follow, attribute_to_follow, max_value):
        assert hasattr(object_to_follow, attribute_to_follow), \
            "Progressbar: The object {} doesn't have an attribute {} that can be followed".format(object_to_follow,
                                                                                                  attribute_to_follow)
        self._object_to_follow = object_to_follow
        self._attribute_to_follow = attribute_to_follow
        self._max_value = max_value
        self._need_redraw = True

    def update(self):
        new_value = getattr(self._object_to_follow, self._attribute_to_follow)

        if new_value != self._current_value:
            self._current_value = new_value
            self._need_redraw = True

    def draw(self, screen):
        # Calculate the width of the bar
        bar_width = 1
        if self._max_value > 0:
            bar_width = max(1, int(float(self._current_value) / self._max_value * self._dimension[0]))

        # Background part
        total_bar = pg.Surface(self._dimension, pg.SRCALPHA)
        total_bar.fill(self._back_color)
        screen.blit(total_bar, self._position)

        # Bar part
        bar = pg.Surface((bar_width, self._dimension[1]))
        bar.fill(self._bar_color)
        screen.blit(bar, self._position)

        # finally, some centered text with the values
        if self._with_text:
            fontSurface = self._font.render(str(self._current_value) + '/' + str(self._max_value), 1, (255, 255, 255))
            screen.blit(fontSurface, (self._position[0] + 10,
                                      self._position[1] + int(float(self._dimension[1] - self._font.get_height()) / 2)))


def rounded_surface(rect, color, radius=1):
    """
    AAfilledRoundedRect(surface,rect,color,radius=0.4)

    surface : destination
    rect    : rectangle
    color   : rgb or rgba
    radius  : 0 <= radius <= 1
    """

    rect = pg.Rect(rect)
    color = pg.Color(*color)
    alpha = color.a
    color.a = 0
    rect.topleft = 0, 0
    rect_surface = pg.Surface(rect.size, pg.SRCALPHA)

    circle = pg.Surface([min(rect.size) * 3] * 2, pg.SRCALPHA)
    pg.draw.ellipse(circle, (0, 0, 0), circle.get_rect(), 0)
    circle = pg.transform.smoothscale(circle, [int(min(rect.size) * radius)] * 2)

    radius = rect_surface.blit(circle, (0, 0))
    radius.bottomright = rect.bottomright
    rect_surface.blit(circle, radius)
    radius.topright = rect.topright
    rect_surface.blit(circle, radius)
    radius.bottomleft = rect.bottomleft
    rect_surface.blit(circle, radius)

    rect_surface.fill((0, 0, 0), rect.inflate(-radius.w, 0))
    rect_surface.fill((0, 0, 0), rect.inflate(0, -radius.h))

    rect_surface.fill(color, special_flags=pg.BLEND_RGBA_MAX)
    rect_surface.fill((255, 255, 255, alpha), special_flags=pg.BLEND_RGBA_MIN)

    return rect_surface


class Label(Widget):
    DEFAULT_OPTIONS = {
        "font_name": default.FONT_NAME,
        "font_size": 14,
        "font_color": (255, 255, 255),  # ignored if a theme is given

        "bg_color": None,  # Transparent if None - ignored if a theme is given

        "text_margin_x": 20,  # Minimum margin on the right & left, only relevant if a background is set (Color/image)
        "text_margin_y": 10,  # Minimum margin on the top & down, only relevant if a background is set (Color/image)
        "text_align_x": "CENTER",
        "text_align_y": "CENTER",

        "dimension": (250, 10),
        "adapt_text_width": True,  # if set to true, will grow the width dimension to the text size
        "adapt_text_height": True,  # if set to true, will grow the width dimension to the text size

        "theme": default.THEME_LIGHT_GRAY,  # the main theme
    }

    def __init__(self, text=None, position=(0, 0), **kwargs):
        Widget.__init__(self)

        original_kwargs = deepcopy(kwargs)
        for key in Label.DEFAULT_OPTIONS:
            self.__setattr__(key, original_kwargs.pop(key, Label.DEFAULT_OPTIONS[key]))
        if len(original_kwargs) != 0:
            print("Warning: unused attributes in Label {}".format(original_kwargs))

        self.position = position

        # Now adapt some parameters
        self.font = GLOBAL.font(self.font_name, self.font_size)

        # Do we have a theme?
        if self.theme:
            border_size = 0
            for border_info in self.theme["borders"]:
                border_size += border_info[0]
            self.text_margin_x = border_size + self.text_margin_x
            self.text_margin_y = border_size + self.text_margin_y
            self.font_color = self.theme["font_color"]

        if not self.theme and not self.bg_color:
            self.text_margin_x = self.text_margin_y = 0

        self.set_text(text)

    def set_text(self, text):
        """Set the text to display."""
        self.text = text
        if self.text is None:
            self.text = " "
        self.update_image()

    def update_image(self):
        """
        Update the surface using the current properties and text.
        Prepare:
        * An image for the font rendered (and its background if it is there)
        * A Rect for the image, already positionned
        *
        """

        font_image = self.font.render(self.text, True, self.font_color)
        font_rect = font_image.get_rect().move(self.position)
        pos_font_x = self.text_margin_x
        pos_font_y = self.text_margin_y

        if not self.adapt_text_width:
            font_rect.width = self.dimension[0] - 2 * self.text_margin_x
        else:
            if font_rect.width < self.dimension[0] - 2 * self.text_margin_x:
                # and we need to reposition the label...
                if self.text_align_x == "LEFT":
                    pos_font_x = self.text_margin_x
                elif self.text_align_x == "RIGHT":
                    pos_font_x = self.dimension[0] - font_rect.width - self.text_margin_x
                else:
                    pos_font_x = int((self.dimension[0] - font_rect.width) / 2)
                font_rect.width = self.dimension[0] - 2 * self.text_margin_x
            else:
                font_rect.width += 2 * self.text_margin_x
                pos_font_x = self.text_margin_x
        if not self.adapt_text_height:
            font_rect.height = self.dimension[1] - 2 * self.text_margin_y
        else:
            font_rect.height = max(font_rect.height, self.dimension[1])

        if self.theme or self.bg_color:
            width_background, height_background = font_rect.width + 2 * self.text_margin_x, \
                                                  font_rect.height + 2 * self.text_margin_y
            background_rect = pg.Rect(self.position, (width_background, height_background))
            font_rect.move_ip(self.text_margin_x, self.text_margin_y)

            if self.bg_color:
                self.image = pg.Surface(background_rect.size, pg.SRCALPHA)
                self.image.fill(self.bg_color)

                self.image.blit(font_image, (pos_font_x, pos_font_y),
                                area=pg.Rect((0, 0), (font_rect.width, font_rect.height)))

            if self.theme:
                rect = pg.Rect((0, 0), background_rect.size)
                margin = 0
                color = (0, 0, 0) # if no border, and we need to add deco, we do a black...

                if self.theme["borders"]:
                    # First, we start by creating a surface, which is the external one.
                    margin = self.theme["borders"][0][0] * 2
                    color = self.theme["borders"][0][1]
                    self.image = rounded_surface(rect, color, radius=self.theme["rounded_angle"])

                    if len(self.theme["borders"]) > 1:
                        for index in range(1, len(self.theme["borders"])):
                            color = self.theme["borders"][index][1]
                            self.image.blit(
                                rounded_surface(rect.inflate(-margin * 2, -margin * 2),
                                                color,
                                                radius=self.theme["rounded_angle"]),
                                (margin, margin)
                            )
                            margin += self.theme["borders"][index][0] * 2
                    # add the internal:
                    self.image.blit(rounded_surface(rect.inflate(-margin*2, -margin*2),
                                                    self.theme["bg_color"],
                                                    radius=self.theme["rounded_angle"]),
                                    (margin, margin))
                elif self.theme["bg_color"]:
                    # We just do something for the background
                    self.image = rounded_surface(rect, self.theme["bg_color"], radius=self.theme["rounded_angle"])

                # add the font:
                self.image.blit(font_image, (pos_font_x, pos_font_y),
                                area=pg.Rect((0, 0), (font_rect.width, font_rect.height)))

                if self.theme["with_decoration"]:
                    # No more than 1 every 75 pixels in average...
                    for i in range(random.randint(0, int(self.image.get_rect().width / 75))):
                        # Top
                        x = random.randint(2 * margin, self.image.get_rect().width - 2 * margin)
                        pg.draw.polygon(self.image, color, [(x, margin), (x+4, margin), (x+2, margin + 2)], 0)
                    # No more than 1 every 75 pixels in average...
                    for i in range(random.randint(0, int(self.image.get_rect().width / 75))):
                        # Bottom
                        x = random.randint(2 * margin, self.image.get_rect().width - 2 * margin)
                        y = self.image.get_rect().height - 1
                        pg.draw.polygon(self.image, color, [(x, y- margin), (x+4, y-margin), (x+2, y-margin - 2)], 0)
                    # No more than 1 every 75 pixels in average...
                    for i in range(random.randint(0, int(self.image.get_rect().height / 75))):
                        # Left
                        y = random.randint(2 * margin, self.image.get_rect().height - 2 * margin)
                        pg.draw.polygon(self.image, color, [(margin, y), (margin, y + 4), (margin + 2, y + 2)], 0)
                    # No more than 1 every 75 pixels in average...
                    for i in range(random.randint(0, int(self.image.get_rect().height / 75))):
                        # Right
                        y = random.randint(2 * margin, self.image.get_rect().height - 2 * margin)
                        x = self.image.get_rect().width - 1
                        pg.draw.polygon(self.image, color, [(x - margin, y), (x - margin, y + 4), (x - margin - 2, y + 2)], 0)

            self.rect = self.image.get_rect().move(self.position)

        else:
            self.image = font_image
            self.rect = font_rect


class Button(Widget):
    """
    A simple Button, based on a label (without an image)
    """
    DEFAULT_OPTIONS = {
        "font_name": default.FONT_NAME,
        "font_size": 14,
        "font_color": (255, 255, 255),

        "bg_color": None,  # Transparent button if None and if no Theme is set

        "text_margin_x": 5,  # Minimum margin on the right & left, only relevant if a background is set (Color/image)
        "text_margin_y": 5,  # Minimum margin on the top & down, only relevant if a background is set (Color/image)
        "text_align_x": "CENTER",
        "text_align_y": "CENTER",

        "dimension": (10, 10),
        "adapt_text_width": True,  # if set to true, will grow the width dimension to the text size
        "adapt_text_height": False,  # if set to true, will grow the height dimension to the text size

        "theme_idle": default.THEME_LIGHT_BROWN,  # the Theme to use when nothing is there
        "theme_hover": default.THEME_DARK_BROWN,  # the Theme to use when the mouse is over
    }

    # Based on pygbutton
    def __init__(self, callback_function=None, text=None, position=(0, 0), **kwargs):

        assert callback_function, "Button defined without callback function"

        Widget.__init__(self)

        original_kwargs = deepcopy(kwargs)
        for key in Button.DEFAULT_OPTIONS:
            self.__setattr__(key, original_kwargs.pop(key, Button.DEFAULT_OPTIONS[key]))
        if len(original_kwargs) != 0:
            print("Warning: unused attributes in Button {}".format(original_kwargs))

        self.position = position
        self.callback_function = callback_function

        state = random.getstate()
        kwargs["theme"] = self.theme_idle
        label = Label(position=position, text=text, **kwargs)
        self.image = self.idle_image = label.image

        random.setstate(state)  # To be sure to have the decoration on the same places...
        kwargs["theme"] = self.theme_hover
        label = Label(position=position, text=text, **kwargs)
        self.hover_image = label.image

        self.rect = label.rect
        self.hover = False

    def handle_event(self, event):
        if event.type == pg.MOUSEBUTTONDOWN and self.hover:
            self.hover = False
            self.callback_function()
        elif event.type == pg.MOUSEMOTION:
            if self.rect.collidepoint(event.pos):
                self.hover = True
            else:
                self.hover = False

    def update(self):
        if self.hover:
            self.image = self.hover_image
        else:
            self.image = self.idle_image


def display_single_message_on_screen(text, position="CENTER", font_size=18, erase_screen_first=True):
    """
    Erase the screen, replace wit a simple message. Use for basic info.
    :param position the position of the message, default "CENTER", can also be "BOTTOM" or "TOP"
    :param font_size the font_size to use
    :param erase_screen_first if set to True, will erase the screen first
    :return:
    """
    # Maybe optimize the stuff below
    font = pg.font.Font(os.path.join(default.FONT_FOLDER, default.FONT_NAME), font_size)

    if erase_screen_first:
        # Erase the screen
        screen = pg.display.get_surface()
        screen.fill(default.BLACK)

    text = font.render(text, True, default.WHITE)
    text_rect = text.get_rect()

    left_x = screen.get_rect().centerx - int(text_rect.width / 2)
    top_y = screen.get_rect().centery - int(text_rect.height / 2)
    if position == "BOTTOM":
        top_y = screen.get_rect().height - text_rect.height
    if position == "TOP":
        top_y = 0
    screen.blit(text, (left_x, top_y))

    # And done...
    pg.display.update()
