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

        self.container_parent = None
        self.id_in_container = None

    def update(self):
        """
        In general this method is not really usefull, but it is called from the master.
        Can be used to prepare the image
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
        """
        assert self.image, "Image doesn't exist so can't blit"
        assert self.rect, "Rect doesn't exist so can't blit"
        screen.blit(self.image, self.rect)

    def move(self, dx, dy):
        """
        Move the widget position according to dx, dy parameters. Perticularly important for composite widgets.
        :param dx: the amount of pixel to move horizontally
        :param dy: the amount of pixel to move vertically
        """


class MouseWidget(Widget):
    """
    Replace the mouse by a nice image.
    """
    CENTER = "center"
    TOP_LEFT = "top_left"
    TOP_RIGHT = "top_right"
    BOTTOM_LEFT = "bottom_left"
    BOTTOM_RIGHT = "bottom_right"

    def __init__(self, image_surface, image_click_position=CENTER):
        """
        Initialize the mouse widget
        :param image_surface: The surface that is used to replace the mouse.
        :param image_click_position: Indicates the place of the image that is used as reference for the click
        """
        Widget.__init__(self)

        self.active = True
        self.click_position = image_click_position
        self.set_image(image_surface, image_click_position=image_click_position)

        pg.mouse.set_visible(not self.active)

    def set_active(self, state):
        """
        Turn on or off the widget, and put it back to the original states
        :param state: True to use the widget, False otherwise
        """
        self.active = state and self.image
        pg.mouse.set_visible(not self.active)

    def set_image(self, image_surface, image_click_position=CENTER):
        """
        Set the image for the mouse cursor
        :param image_surface: The surface that is used to replace the mouse.
        :param image_click_position: Indicates the place of the image that is used as reference for the click
        """
        if image_surface:
            assert type(image_surface) is pg.Surface, "Image surface used for mouse widget is not a pygame Surface"
            self.image = image_surface
            self.rect = image_surface.get_rect()
            self.click_position = image_click_position
        else:
            self.active = False
        pg.mouse.set_visible(not self.active)

    def handle_event(self, event):
        if self.active:
            if event.type == pg.MOUSEMOTION:
                if self.click_position == MouseWidget.CENTER:
                    self.rect.center = event.pos
                elif self.click_position == MouseWidget.TOP_LEFT:
                    self.rect.topleft = event.pos
                elif self.click_position == MouseWidget.TOP_RIGHT:
                    self.rect.topright = event.pos
                elif self.click_position == MouseWidget.BOTTOM_LEFT:
                    self.rect.bottomleft = event.pos
                elif self.click_position == MouseWidget.BOTTOM_RIGHT:
                    self.rect.bottomright = event.pos
                else:
                    raise Exception("Invalid click position on image: {}".format(self.click_position))


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


class Label2(Widget):
    DEFAULT_OPTIONS = {
        "font_name": default.FONT_NAME,
        "font_size": 14,
        "font_color": (255, 255, 255),  # ignored if a theme is given

        "bg_color": None,  # Transparent if None - ignored if a theme is given

        "text_margin_x": 10,  # Minimum margin on the right & left, only relevant if a background is set (Color/image)
        "text_margin_y": 10,  # Minimum margin on the top & down, only relevant if a background is set (Color/image)
        "text_align_x": "LEFT",
        "text_align_y": "CENTER",

        # To set the theme
        # "theme": default.THEME_LIGHT_GRAY,  # the main theme or None
        "theme": None,  # the main theme or None

        # To make it multiline and scrollable
        "scrollable_position": "RIGHT",  # The position either at the rihgt or at the left
        "scrollable_size": 30,  # the space dedicated to the arrows
        "scrollable_color": (0, 0, 0),  # the color for the arrow - if no theme is used
    }

    def __init__(self,
                 text=None,
                 position=(0, 0),
                 dimension=(80, 20), # preferred dimensions of the total widget.
                 # Note that x dimension might change with adapt_text_width parameter,
                 # and y_dimension changes if set to multiline and grow_height
                 style_dict=None,
                 grow_width_with_text=False,
                 grow_height_with_text=False,
                 multiline=False,
                 scrollable=False):

        Widget.__init__(self)
        self.text = None

        self.style_dict = style_dict or {}
        assert type(self.style_dict) is dict, "Style dict must be a dictionnary if provided"

        self.text_rect = None  # The text rect is the rect for the text. The widget rect is defined in parent.
        self.rect = None

        self.text_image = None  # This is the pre_rendered image of teh text
        self.background_image = None  # This is the pre_rendered image of the background
        self.image = None  # Note: final image = backgound image + text image

        # Set the standard attributes
        self.position = position
        self.dimension = [dimension[0],
                          dimension[1]]

        self.multiline = multiline
        self.scrollable = scrollable
        self.grow_width_with_text = grow_width_with_text
        self.grow_height_with_text = grow_height_with_text

        # Get the style attributes
        self.font = GLOBAL.font(self.style_dict.get("font_name", Label2.DEFAULT_OPTIONS["font_name"]),
                                self.style_dict.get("font_size", Label2.DEFAULT_OPTIONS["font_size"]))
        self.theme = self.style_dict.get("theme", Label2.DEFAULT_OPTIONS["theme"])
        self.decoration_instructions = []

        if self.theme:
            assert type(self.theme) is dict, "Theme must be a dictionnary if set"
            self.font_color = self.theme.get("font_color",
                                             self.style_dict.get("font_color",
                                                                 Label2.DEFAULT_OPTIONS["font_color"]))
        else:
            self.font_color = self.style_dict.get("font_color", Label2.DEFAULT_OPTIONS["font_color"])

        # Margins contain the predefined margin + the margin from the border (if theme) + the margin from the scrollable
        self.margin_x_left = self.margin_x_right = 0
        self.margin_y_top = self.margin_y_bottom = 0
        self._compute_margin()

        self.set_text(text, force_recreate_decoration=True)

    def set_text(self, text, recreate_background=True, force_recreate_decoration=False):
        """
        Compute the text_image and the text_rect
        :param text:
        :param recreate_background:
        :param force_recreate_decoration:
        :return:
        """
        self.text = text

        if self.multiline:
            #TODO
            pass
        else:
            self.text_image = self.font.render(text, True, self.font_color)
            self.text_rect = self.text_image.get_rect()

        if recreate_background:
            self._adjust_dimension()
            self._create_background(force_recreate_decoration=force_recreate_decoration)

        # Now we can create the final image
        self.image = self.background_image.copy()
        self.image.blit(self.text_image, (self.margin_x_left, self.margin_y_top), area=pg.Rect((0, 0),
                                                                                               self.text_rect.size))
        self.rect = self.image.get_rect()
        self.rect.topleft = self.position


    def _compute_margin(self):
        """
        Set margin_x left/right, and margin_y top/bottom
        :return:
        """
        if self.theme:
            self.margin_x_left = self.margin_x_right = self.style_dict.get("text_margin_x",
                                                                      Label2.DEFAULT_OPTIONS["text_margin_x"])
            self.margin_y_top = self.margin_y_bottom = self.style_dict.get("text_margin_y",
                                                                      Label2.DEFAULT_OPTIONS["text_margin_y"])
            for border_info in self.theme["borders"]:
                self.margin_x_left += border_info[0]
                self.margin_x_right += border_info[0]
                self.margin_y_top += border_info[0]
                self.margin_y_bottom += border_info[0]
        elif "bg_color" in self.style_dict:
            self.margin_x_left = self.margin_x_right = self.style_dict.get("text_margin_x",
                                                                      Label2.DEFAULT_OPTIONS["text_margin_x"])
            self.margin_y_top = self.margin_y_bottom = self.style_dict.get("text_margin_y",
                                                                      Label2.DEFAULT_OPTIONS["text_margin_y"])
        if self.scrollable:
            if self.style_dict.get("scrollable_position", Label2.DEFAULT_OPTIONS["scrollable_position"]) == "RIGHT":
                self.margin_x_right += self.style_dict.get("scrollable_size", Label2.DEFAULT_OPTIONS["scrollable_size"])
            else:
                self.margin_x_left += self.style_dict.get("scrollable_size", Label2.DEFAULT_OPTIONS["scrollable_size"])


    def _adjust_dimension(self):
        """
        Change the dimension of the total widget to accomodate the text and the margin
        Assumes that the text_rect has been setup previously
        :return:
        """
        if self.grow_width_with_text:
            self.dimension[0] = max(self.dimension[0], self.text_rect.width + self.margin_x_left + self.margin_x_right)
        if self.grow_height_with_text:
            self.dimension[1] = max(self.dimension[1], self.text_rect.height + self.margin_y_bottom + self.margin_y_top)

    def _create_background(self, force_recreate_decoration=False):
        # this assumes that dimension is correctly set
        self.background_image = pg.Surface(self.dimension, pg.SRCALPHA)

        bg_color = self.style_dict.get("bg_color", Label2.DEFAULT_OPTIONS["bg_color"])
        if bg_color:
            self.background_image.fill(bg_color)
        elif self.theme:
            rect = pg.Rect((0, 0), self.dimension)
            if self.theme["borders"]:
                # First, we start by creating a surface, which is the external one.

                margin = self.theme["borders"][0][0]
                color = self.theme["borders"][0][1]
                self.background_image = rounded_surface(rect, color, radius=self.theme["rounded_angle"])

                if len(self.theme["borders"]) > 1:
                    for index in range(1, len(self.theme["borders"])):
                        color = self.theme["borders"][index][1]
                        self.background_image.blit(
                            rounded_surface(rect.inflate(-margin * 2, -margin * 2),
                                            color,
                                            radius=self.theme["rounded_angle"]),
                            (margin, margin)
                        )
                        margin += self.theme["borders"][index][0]
                # add the internal:
                self.background_image.blit(rounded_surface(rect.inflate(-margin * 2, -margin * 2),
                                                self.theme["bg_color"],
                                                radius=self.theme["rounded_angle"]),
                                (margin, margin))

            # We finally add the decoration
            #TODO

            elif self.theme["bg_color"]:
                # We just do something for the background
                self.background_image = rounded_surface(rect, self.theme["bg_color"], radius=self.theme["rounded_angle"])

        if self.scrollable:
            #TODO Add the up/down arrow
            pass

        if force_recreate_decoration:
            #TODO Set the decoration
            pass

        self.rect = self.background_image.get_rect()

class Label(Widget):

    DEFAULT_OPTIONS = {
        "font_name": default.FONT_NAME,
        "font_size": 14,
        "font_color": (255, 255, 255),  # ignored if a theme is given

        "bg_color": None,  # Transparent if None - ignored if a theme is given

        "text_margin_x": 10,  # Minimum margin on the right & left, only relevant if a background is set (Color/image)
        "text_margin_y": 10,  # Minimum margin on the top & down, only relevant if a background is set (Color/image)
        "text_align_x": "LEFT",
        "text_align_y": "CENTER",

        "dimension": (20, 10),
        "adapt_text_width": True,  # if set to true, will grow the width dimension to the text size
        "adapt_text_height": True,  # if set to true, will grow the width dimension to the text size

        # To set the theme
        "theme": default.THEME_LIGHT_GRAY,  # the main theme

        # To make it multiline
        "multiline" : False,  # if set to True will potentially split the text
        "char_limit" : 42,
        "multiline_align": "LEFT",

        # To make it multiline and scrollable
        "scrollable" : False,
        "scrollable_position": "RIGHT",  # The position either at the rihgt or at the left
        "scrollable_size" : 30,  # the space dedicated to the arrows
        "scrollable_color" : (0,0,0),  # the color for the arrow - if no theme is used
        "font_dimension": (0,0)
    }

    def __init__(self, text=None, position=(0, 0), **kwargs):
        Widget.__init__(self)

        original_kwargs = deepcopy(kwargs)
        for key in Label.DEFAULT_OPTIONS:
            self.__setattr__(key, original_kwargs.pop(key, Label.DEFAULT_OPTIONS[key]))
        if len(original_kwargs) != 0:
            print("Warning: unused attributes in Label {}".format(original_kwargs))

        if self.multiline:
            assert self.char_limit is not None, "Multiline set in labels without char_limit"
        if self.scrollable:
            assert self.multiline, "Scrollable needs to be multiline"
            assert self.scrollable_size > 20, "Scrollable size needs to be greater than 20"

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

        if self.scrollable:
            self.adapt_text_width = False
            self.adapt_text_height = False

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
        font_image = None
        height_scrollable = pos_scrollable_x = 0 # pos_scrolable is inside the font image

        if not self.multiline:
            font_image = self.font.render(self.text, True, self.font_color)
        else:
            lines = wrap_text(self.text, self.char_limit)
            label_images = [self.font.render(line, True, self.font_color) for line in lines]
            if not self.scrollable:
                width = max([label.get_rect().width for label in label_images])
                height = sum([label.get_rect().height for label in label_images])
                height_scrollable = min([label.get_rect().height for label in label_images])
            else:
                width = self.font_dimension[0]
                height= self.font_dimension[1]
            font_image = pg.Surface((width, height), pg.SRCALPHA)
            y = 0
            for label in label_images:
                x = 0
                if self.multiline_align == "RIGHT":
                    x = width - label.get_rect().width
                elif self.multiline_align == "CENTER":
                    x = int((width - label.get_rect().width) / 2)
                font_image.blit(label, (x, y))
                y += label.get_rect().height

        font_rect = font_image.get_rect().move(self.position)

        pos_font_x = self.text_margin_x
        pos_font_y = self.text_margin_y

        if not self.adapt_text_width:
            if not self.scrollable:
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
                pos_font_x = self.text_margin_x
        if not self.adapt_text_height:
            if not self.scrollable:
                font_rect.height = self.dimension[1] - 2 * self.text_margin_y
        else:
            font_rect.height = max(font_rect.height, self.dimension[1])

        if self.scrollable:
            pos_scrollable_x = 10
            if self.scrollable_position == "RIGHT":
                pos_scrollable_x += font_rect.width

            font_image_tmp = pg.Surface((font_rect.width + self.scrollable_size, font_rect.height), pg.SRCALPHA)
            font_image_tmp.blit(font_image, (0, 0))
            font_image = font_image_tmp

            font_rect = font_image.get_rect()
            color = self.scrollable_color
            if self.theme and self.theme["borders"]:
                color = self.theme["borders"][-1][1]

            pg.draw.polygon(font_image, color, ((pos_scrollable_x, 12), (pos_scrollable_x+10, 12), (pos_scrollable_x+5, 0)), 0)
            pg.draw.polygon(font_image, color, ((pos_scrollable_x, font_rect.height - 14), (pos_scrollable_x+10, font_rect.height - 14), (pos_scrollable_x+5, font_rect.height - 2)), 0)

            self.scroll_top_rect = pg.Rect((pos_scrollable_x, 0), (10, 12)).move(self.position)
            self.scroll_bottom_rect = pg.Rect((pos_scrollable_x, font_rect.height - 14), (10, 12)).move(self.position)

        if self.theme or self.bg_color:
            width_background, height_background = font_rect.width + 2 * self.text_margin_x, \
                                                  font_rect.height + 2 * self.text_margin_y
            background_rect = pg.Rect(self.position, (width_background, height_background))

            if self.scrollable:
                self.scroll_top_rect = self.scroll_top_rect.move((self.text_margin_x, self.text_margin_y))
                self.scroll_bottom_rect = self.scroll_bottom_rect.move((self.text_margin_x, self.text_margin_y))


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
                    if not hasattr(self, "decoration_instruction") or len(self.decoration_instruction) == 0:
                        self.decoration_instruction = []
                        for i in range(random.randint(0, int(self.image.get_rect().width / 75))):
                            # Top
                            x = random.randint(2 * margin, self.image.get_rect().width - 2 * margin)
                            self.decoration_instruction.append("pg.draw.polygon(self.image, color, [({x}, {margin}), ({x}+4, {margin}), ({x}+2, {margin} + 2)], 0)".format(x=x, margin=margin))
                        # No more than 1 every 75 pixels in average...
                        for i in range(random.randint(0, int(self.image.get_rect().width / 75))):
                            # Bottom
                            x = random.randint(2 * margin, self.image.get_rect().width - 2 * margin)
                            y = self.image.get_rect().height - 1
                            self.decoration_instruction.append(
                                "pg.draw.polygon(self.image, color, [({x}, {y}-{margin}), ({x}+4, {y}-{margin}), ({x}+2, {y}-{margin}-2)], 0)".format(x=x, margin=margin, y=y))
                        # No more than 1 every 75 pixels in average...
                        for i in range(random.randint(0, int(self.image.get_rect().height / 75))):
                            # Left
                            y = random.randint(2 * margin, self.image.get_rect().height - 2 * margin)
                            self.decoration_instruction.append(
                                "pg.draw.polygon(self.image, color, [({margin}, {y}), ({margin}, {y}+4), ({margin}+2, {y}+2)], 0)".format(y=y, margin=margin))
                        # No more than 1 every 75 pixels in average...
                        for i in range(random.randint(0, int(self.image.get_rect().height / 75))):
                            # Right
                            y = random.randint(2 * margin, self.image.get_rect().height - 2 * margin)
                            x = self.image.get_rect().width - 1
                            self.decoration_instruction.append("pg.draw.polygon(self.image, color, [({x}-{margin},{y}), ({x}-{margin},{y}+4), ({x}-{margin}-2,{y}+2)], 0)".format(x=x, margin=margin, y=y))

                    for instruction in self.decoration_instruction:
                        exec(instruction)

            self.rect = self.image.get_rect().move(self.position)

        else:
            self.image = font_image
            self.rect = font_rect



#Helper function for MultiLineLabel class
def wrap_text(text, char_limit, separator=" "):
    """Splits a string into a list of strings no longer than char_limit."""
    if text is None:
        text = ""
    words = text.split(separator)
    lines = []
    current_line = []
    current_length = 0
    for word in words:
        if len(word) + current_length <= char_limit:
            current_length += len(word) + len(separator)
            current_line.append(word)
        else:
            lines.append(separator.join(current_line))
            current_line = [word]
            current_length = len(word) + len(separator)
    if current_line:
        lines.append(separator.join(current_line))
    return lines

#Helper function for MultiLineLabel class
def join_text(lines, separator=' '):
    """unit a list of string with the separator in between"""
    if lines is None:
        return ""

    res = separator.join(lines)
    return res.strip(separator)

class MultiLineLabel(Label):

    def __init__(self, text=None, position=(0, 0), char_limit=42, multiline_align="LEFT", **kwargs):
        Label.__init__(self, text=text, position=position, multiline=True, multiline_align=multiline_align,
                       char_limit=char_limit, **kwargs)


class ScrollableMultiLineLabel(MultiLineLabel):

    def __init__(self, text=None, lines_to_display=3, position=(0,0), char_limit=30, multiline_align="LEFT", scrollable_position="RIGHT", scrollable_color=(0,0,0), scrollable_size=21, **kwargs):
        lines = wrap_text(text, char_limit=char_limit)
        temp_text = None
        if len(lines) > lines_to_display:
            temp_text = join_text(lines[0:lines_to_display])
        else:
            temp_text = text

        # FIXING KWARGS DIMENSION
        font_name = kwargs.get("font_name", default.FONT_NAME)
        font_size = kwargs.get("font_size", 14)
        font = GLOBAL.font(font_name, font_size)
        test = ""
        for i in range(char_limit):
            test += 'W'
        font_image = font.render(test, True, (0, 0, 0))
        (width, height) = font_image.get_rect().size
        kwargs["font_dimension"] = (width, 3 * height)

        self.scroll_top_rect = self.scroll_bottom_rect = None
        MultiLineLabel.__init__(self, text=temp_text, position=position, scrollable=True, char_limit=char_limit, multiline_align=multiline_align, scrollable_color=scrollable_color, scrollable_position=scrollable_position, scrollable_size=scrollable_size, **kwargs)
        self.longtext = text
        self.first_line_to_display = 0
        self.lines_to_display = lines_to_display

    def handle_event(self, event):
        if event.type == pg.MOUSEBUTTONDOWN:
            if self.scroll_top_rect.collidepoint(event.pos):
                self.scroll("UP")
            elif self.scroll_bottom_rect.collidepoint(event.pos):
                self.scroll("BOTTOM")

    def add_text(self, text):
        self.longtext += text

    def scroll(self, direction):
        lines = wrap_text(self.longtext, char_limit=self.char_limit)

        if direction == "UP":
            self.first_line_to_display = max(0, self.first_line_to_display - 1)
        elif direction == "BOTTOM":
            self.first_line_to_display = min (self.first_line_to_display + 1, len(lines) - self.lines_to_display)

        if len(lines) > self.lines_to_display:
            temp_text = join_text(lines[self.first_line_to_display:self.first_line_to_display + self.lines_to_display])
            self.set_text(temp_text)
        else:
            self.set_text(self.longtext)


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
