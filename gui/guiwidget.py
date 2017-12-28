import pygame as pg
import os
import default
import random

from shared import GLOBAL


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
        pass


class Style:
    """
    Handle the default style options
    """
    # Themes for Buttons, labels...
    THEME_LIGHT_GRAY = {
        "rounded_angle": 0.1,  # 0 = no angle, 1 = full angle
        "with_decoration": True,  # This adds small triangles
        "borders": [(4, (233, 233, 233)), (4, (203, 203, 203))],  # list of margin + colors (external to int)
        "bg_color": (229, 229, 229),
        "font_color": (155, 157, 173)
    }
    THEME_DARK_GRAY = {
        "rounded_angle": 0.1,  # 0 = no angle, 1 = full angle
        "with_decoration": True,  # This adds small triangles
        "borders": [(4, (97, 99, 116)), (4, (155, 157, 173))],  # list of margin + colors (external to int)
        "bg_color": (131, 135, 150),
        "font_color": (233, 233, 233)
    }
    THEME_LIGHT_BROWN = {
        "rounded_angle": 0.1,  # 0 = no angle, 1 = full angle
        "with_decoration": True,  # This adds small triangles
        "borders": [(4, (217, 205, 175)), (4, (177, 160, 119))],  # list of margin + colors (external to int)
        "bg_color": (211, 191, 143),
        "font_color": (155, 157, 173)
    }
    THEME_DARK_BROWN = {
        "rounded_angle": 0.1,  # 0 = no angle, 1 = full angle
        "with_decoration": True,  # This adds small triangles
        "borders": [(4, (136, 102, 68)), (4, (183, 145, 106))],  # list of margin + colors (external to int)
        "bg_color": (151, 113, 74),
        "font_color": (233, 233, 233)
    }

    @staticmethod
    def set_style(theme="GRAY"):
        font_name = default.FONT_NAME
        theme_default_hover = theme_default = None

        if theme == "GRAY":
            theme_default = Style.THEME_LIGHT_GRAY
            theme_default_hover = Style.THEME_DARK_GRAY
        if theme == "BROWN":
            theme_default = Style.THEME_LIGHT_BROWN
            theme_default_hover = Style.THEME_DARK_BROWN

        TextButton.DEFAULT_OPTIONS["font_name"] = font_name
        TextButton.DEFAULT_OPTIONS["theme_hover"] = theme_default_hover
        TextButton.DEFAULT_OPTIONS["theme_idle"] = theme_default

        Label.DEFAULT_OPTIONS["font_name"] = font_name
        Label.DEFAULT_OPTIONS["theme"] = theme_default


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
            fontsurface = self._font.render(str(self._current_value) + '/' + str(self._max_value), 1, (255, 255, 255))
            screen.blit(fontsurface, (self._position[0] + 10,
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

        "text_margin_x": 5,  # Minimum margin on the right & left, only relevant if a background is set (Color/image)
        "text_margin_y": 5,  # Minimum margin on the top & down, only relevant if a background is set (Color/image)
        "text_align_x": "LEFT",
        "text_align_y": "TOP",

        # To set the theme
        "theme": None,  # the main theme or None

        # To make it multiline and scrollable
        "scrollable_position": "RIGHT",  # The position either at the rihgt or at the left
        "scrollable_size": 25,  # the space dedicated to the arrows
        "scrollable_color": (0, 0, 0),  # the color for the arrow - if no theme is used
    }

    def __init__(self,
                 text=None,
                 position=(0, 0),
                 dimension=(10, 10),  # preferred dimensions of the total widget.
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

        if self.scrollable:
            assert self.multiline, "A scrollable label needs to be multiline"
            scrollable_size = self.style_dict.get("scrollable_size", Label.DEFAULT_OPTIONS["scrollable_size"])
            assert scrollable_size > 20, "Scrollable size needs to be greater than 20"
            self.scroll_bottom_rect = self.scroll_top_rect = None
            self.scroll_index = 0

        if self.multiline:
            assert not self.grow_width_with_text, "Multiline label can not have automatic width adjustment"
            self.number_of_lines_to_display = 0
            self.number_of_lines = 0

        # Get the style attributes
        self.font = GLOBAL.font(self.style_dict.get("font_name", Label.DEFAULT_OPTIONS["font_name"]),
                                self.style_dict.get("font_size", Label.DEFAULT_OPTIONS["font_size"]))
        self.theme = self.style_dict.get("theme", Label.DEFAULT_OPTIONS["theme"])
        self.decoration_instructions = []

        if self.theme:
            assert type(self.theme) is dict, "Theme must be a dictionnary if set"
            self.font_color = self.theme.get("font_color",
                                             self.style_dict.get("font_color",
                                                                 Label.DEFAULT_OPTIONS["font_color"]))
        else:
            self.font_color = self.style_dict.get("font_color", Label.DEFAULT_OPTIONS["font_color"])

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
        if self.text is None:
            self.text = " "

        if self.multiline:
            self._compute_multiline_text_image(scroll_index=self.scroll_index)
        else:
            self.text_image = self.font.render(text, True, self.font_color)

        self.text_rect = self.text_image.get_rect()

        if recreate_background:
            self._adjust_dimension()
            self._create_background(force_recreate_decoration=force_recreate_decoration)

        # Now we can create the final image: we copy the background and the text
        self.image = self.background_image.copy()
        self.rect = self.image.get_rect()

        self._blit_text_on_image()

        # And we finally move to the position
        self.rect.topleft = self.position

    def _blit_text_on_image(self):
        # We test to know if we have extra space...
        position_to_blit_text = [self.margin_x_left, self.margin_y_top]
        # Test horizontally:
        extra_space_x = self.rect.width - (self.text_rect.width + self.margin_x_left + self.margin_x_right)
        if extra_space_x > 0:
            position_x = self.style_dict.get("text_align_x", Label.DEFAULT_OPTIONS["text_align_x"])
            if position_x == "CENTER":
                position_to_blit_text[0] += int(extra_space_x / 2)
            elif position_x == "RIGHT":
                position_to_blit_text[0] += extra_space_x
        extra_space_y = self.rect.height - (self.text_rect.height + self.margin_y_top + self.margin_y_bottom)
        if extra_space_y > 0:
            position_y = self.style_dict.get("text_align_y", Label.DEFAULT_OPTIONS["text_align_y"])
            if position_y == "CENTER":
                position_to_blit_text[1] += int(extra_space_y / 2)
            elif position_y == "BOTTOM":
                position_to_blit_text[1] += extra_space_y

        text_dimension_to_blit = (
            max(self.rect.width - self.margin_x_left - self.margin_x_right, 0),
            max(self.rect.height - self.margin_y_top - self.margin_y_bottom, 0)
        )
        self.image.blit(self.text_image, position_to_blit_text, area=pg.Rect((0, 0),
                                                                             text_dimension_to_blit))

    def _compute_multiline_text_image(self, scroll_index=0):

        available_dimension_x = self.dimension[0] - self.margin_x_left - self.margin_x_right
        assert available_dimension_x > 20, "X dimension not set or too small"
        lines = self._wrap_text(available_dimension_x)
        line_images = [
            self.font.render(line, True, self.font_color) for line in lines
        ]
        self.number_of_lines = len(line_images)
        if len(line_images) <= 1 and self.scrollable:
            # If it is not really a multiline, remove the scrollable part
            self.scrollable = False
            self._compute_margin()
            available_dimension_x = self.dimension[0] - self.margin_x_left - self.margin_x_right

        heights = [line_image.get_rect().height for line_image in line_images]
        available_dimension_y = self.dimension[1] - self.margin_y_top - self.margin_y_bottom
        biggest_height = max(heights)
        assert available_dimension_y >= biggest_height, "Y dimension too small for multiline"
        self.number_of_lines_to_display = int(available_dimension_y / biggest_height)

        self.text_image = pg.Surface((available_dimension_x, available_dimension_y), pg.SRCALPHA)
        position_x = self.style_dict.get("text_align_x", Label.DEFAULT_OPTIONS["text_align_x"])
        position_y = self.style_dict.get("text_align_y", Label.DEFAULT_OPTIONS["text_align_y"])
        shift_y = 0
        if position_y == "CENTER":
            shift_y = int((available_dimension_y - sum(heights)) / 2)
        elif position_y == "BOTTOM":
            shift_y = available_dimension_y - sum(heights)

        for i in range(scroll_index, scroll_index + self.number_of_lines_to_display):
            if i < len(line_images):
                if position_x == "CENTER":
                    self.text_image.blit(line_images[i],
                                         (int((available_dimension_x - line_images[i].get_rect().width) / 2),
                                          (i - scroll_index) * biggest_height + shift_y))
                elif position_x == "RIGHT":
                    self.text_image.blit(line_images[i],
                                         (available_dimension_x - line_images[i].get_rect().width,
                                          (i - scroll_index) * biggest_height + shift_y))
                else:
                    self.text_image.blit(line_images[i], (0, (i - scroll_index) * biggest_height + shift_y))

    def _compute_margin(self):
        """
        Set margin_x left/right, and margin_y top/bottom
        :return:
        """
        if self.theme:
            self.margin_x_left = self.margin_x_right = self.style_dict.get("text_margin_x",
                                                                           Label.DEFAULT_OPTIONS["text_margin_x"])
            self.margin_y_top = self.margin_y_bottom = self.style_dict.get("text_margin_y",
                                                                           Label.DEFAULT_OPTIONS["text_margin_y"])
            for border_info in self.theme["borders"]:
                self.margin_x_left += border_info[0]
                self.margin_x_right += border_info[0]
                self.margin_y_top += border_info[0]
                self.margin_y_bottom += border_info[0]
        elif "bg_color" in self.style_dict:
            self.margin_x_left = self.margin_x_right = self.style_dict.get("text_margin_x",
                                                                           Label.DEFAULT_OPTIONS["text_margin_x"])
            self.margin_y_top = self.margin_y_bottom = self.style_dict.get("text_margin_y",
                                                                           Label.DEFAULT_OPTIONS["text_margin_y"])
        if self.scrollable:
            if self.style_dict.get("scrollable_position", Label.DEFAULT_OPTIONS["scrollable_position"]) == "RIGHT":
                self.margin_x_right += self.style_dict.get("scrollable_size", Label.DEFAULT_OPTIONS["scrollable_size"])
            else:
                self.margin_x_left += self.style_dict.get("scrollable_size", Label.DEFAULT_OPTIONS["scrollable_size"])

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

        if self.dimension[0] < self.margin_x_left + self.margin_x_right + 1:
            self.dimension[0] = self.margin_x_left + self.margin_x_right + 1
        if self.dimension[1] < self.margin_y_top + self.margin_y_bottom + 1:
            self.dimension[1] = self.margin_y_top + self.margin_y_bottom + 1

    def _create_background(self, force_recreate_decoration=False):
        # this assumes that dimension is correctly set
        self.background_image = pg.Surface(self.dimension, pg.SRCALPHA)

        bg_color = self.style_dict.get("bg_color", Label.DEFAULT_OPTIONS["bg_color"])
        margin = 0  # Also used in decoration later

        if self.theme:
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

            elif self.theme["bg_color"]:
                # We just do something for the background
                self.background_image = rounded_surface(rect, self.theme["bg_color"],
                                                        radius=self.theme["rounded_angle"])
        elif bg_color:
            self.background_image.fill(bg_color)

        if self.scrollable:
            scrollable_position = self.style_dict.get("scrollable_position",
                                                      Label.DEFAULT_OPTIONS["scrollable_position"])
            scrollable_color = self.style_dict.get("scrollable_color", Label.DEFAULT_OPTIONS["scrollable_color"])
            if self.theme and self.theme["borders"]:
                scrollable_color = self.theme["borders"][-1][1]

            pos_scrollable_x = 0
            if scrollable_position == "LEFT":
                pos_scrollable_x = self.margin_x_left - 15
            elif scrollable_position == "RIGHT":
                pos_scrollable_x = self.background_image.get_rect().width - (self.margin_x_right - 15)

            # Top arrow - aligned with margin_y_top
            y_arrow_up_ref = self.margin_y_top
            pg.draw.polygon(self.background_image, scrollable_color,
                            ((pos_scrollable_x, y_arrow_up_ref + 12),
                             (pos_scrollable_x + 10, y_arrow_up_ref + 12),
                             (pos_scrollable_x + 5, y_arrow_up_ref)), 0)
            self.scroll_top_rect = pg.Rect((pos_scrollable_x, self.margin_y_top), (10, 12)).move(self.position)

            # Bottom arrow - aligned with margin_y_bottom
            y_arrow_bottom_ref = self.background_image.get_rect().height - self.margin_y_bottom
            pg.draw.polygon(self.background_image, scrollable_color, (
                (pos_scrollable_x, y_arrow_bottom_ref - 12),
                (pos_scrollable_x + 10, y_arrow_bottom_ref - 12),
                (pos_scrollable_x + 5, y_arrow_bottom_ref)), 0)
            self.scroll_bottom_rect = pg.Rect((pos_scrollable_x, y_arrow_bottom_ref - 12), (10, 12)).move(self.position)

        if self.theme and "with_decoration" in self.theme and self.theme["with_decoration"]:
            if force_recreate_decoration:
                self.decoration_instruction = []
                # No more than 1 every 75 pixels in average...
                for i in range(random.randint(0, int(self.background_image.get_rect().width / 75))):
                    # Top
                    x = random.randint(2 * margin, self.background_image.get_rect().width - 2 * margin)
                    self.decoration_instruction.append(
                        "pg.draw.polygon(self.background_image, color, "
                        "[({x}, {margin}), ({x}+4, {margin}), ({x}+2, {margin} + 2)], 0)".format(
                            x=x, margin=margin))
                for i in range(random.randint(0, int(self.background_image.get_rect().width / 75))):
                    # Bottom
                    x = random.randint(2 * margin, self.background_image.get_rect().width - 2 * margin)
                    y = self.background_image.get_rect().height - 1
                    self.decoration_instruction.append(
                        "pg.draw.polygon(self.background_image, color, "
                        "[({x}, {y}-{margin}), ({x}+4, {y}-{margin}), ({x}+2, {y}-{margin}-2)], 0)".format(
                            x=x, margin=margin, y=y))
                for i in range(random.randint(0, int(self.background_image.get_rect().height / 75))):
                    # Left
                    y = random.randint(2 * margin, self.background_image.get_rect().height - 2 * margin)
                    self.decoration_instruction.append(
                        "pg.draw.polygon(self.background_image, color, "
                        "[({margin}, {y}), ({margin}, {y}+4), ({margin}+2, {y}+2)], 0)".format(
                            y=y, margin=margin))
                # No more than 1 every 75 pixels in average...
                for i in range(random.randint(0, int(self.background_image.get_rect().height / 75))):
                    # Right
                    y = random.randint(2 * margin, self.background_image.get_rect().height - 2 * margin)
                    x = self.background_image.get_rect().width - 1
                    self.decoration_instruction.append(
                        "pg.draw.polygon(self.background_image, color, "
                        "[({x}-{margin},{y}), ({x}-{margin},{y}+4), ({x}-{margin}-2,{y}+2)], 0)".format(
                            x=x, margin=margin, y=y))

            for instruction in self.decoration_instruction:
                exec(instruction)

    def _wrap_text(self, available_dimension, separator=" "):
        """
        Splits a string into a list of strings which font representation is no longer than available dimension.
        """
        if self.text is None:
            self.text = ""
        words = self.text.split(separator)
        word_lengths = []
        for word in words:
            length = self.font.render(word, True, (0, 0, 0)).get_rect().width
            word_lengths.append(length)
            if length > available_dimension:
                raise Exception("Dimension too small for word! {}".format(word))

        separator_length = self.font.render(separator, True, (0, 0, 0)).get_rect().width

        lines = []
        current_line = ""
        current_length = 0

        for counter, word in enumerate(words):
            word_length = word_lengths[counter]
            if current_length == 0:
                current_length = word_length
                current_line = word
            else:
                if current_length + separator_length + word_length <= available_dimension:
                    current_line = current_line + separator + word
                    current_length += separator_length + word_length
                else:
                    lines.append(current_line)
                    current_line = word
                    current_length = word_length
        if current_line != "":
            lines.append(current_line)

        return lines

    def handle_event(self, event):
        if event.type == pg.MOUSEBUTTONDOWN:
            if self.scroll_top_rect.collidepoint(event.pos):
                self.scroll("UP")
            elif self.scroll_bottom_rect.collidepoint(event.pos):
                self.scroll("BOTTOM")

    def add_text(self, text):
        self.set_text(self.text + text)

    def scroll(self, direction):
        if direction == "UP":
            self.scroll_index = max(0, self.scroll_index - 1)
        elif direction == "BOTTOM":
            self.scroll_index = min(self.scroll_index + 1, self.number_of_lines - self.number_of_lines_to_display)
        self.set_text(self.text, recreate_background=False)

    def move(self, dx, dy):
        self.position = (self.position[0] + dx,
                         self.position[1] + dy)
        self.rect.move_ip(dx, dy)
        if self.scrollable:
            self.scroll_bottom_rect.move_ip(dx, dy)
            self.scroll_top_rect.mov(dx, dy)


class TextButton(Widget):
    """
    A simple Button, based on a label (without an image)
    """
    DEFAULT_OPTIONS = {
        "font_name": default.FONT_NAME,
        "font_size": 14,

        "text_margin_x": 5,  # Minimum margin on the right & left, only relevant if a background is set (Color/image)
        "text_margin_y": 5,  # Minimum margin on the top & down, only relevant if a background is set (Color/image)
        "text_align_x": "LEFT",
        "text_align_y": "TOP",

        "font_color_idle": (0, 0, 0),
        "font_color_hover": (255, 0, 0),

        "bg_color_idle": (255, 255, 255),
        "bg_color_hover": (0, 255, 255),

        # To set the theme
        "theme_idle": None,  # the Theme to use when nothing is there
        "theme_hover": None,  # the Theme to use when the mouse is over
    }

    def __init__(self,
                 callback_function=None,
                 text=None,
                 position=(0, 0),
                 dimension=(10, 10),
                 style_dict=None,
                 grow_width_with_text=False,
                 grow_height_with_text=True,
                 multiline=False):

        assert callback_function, "Button defined without callback function"

        Widget.__init__(self)

        self.position = position
        self.callback_function = callback_function
        self.dimension = dimension
        self.style_dict = style_dict or {}

        state = random.getstate()
        self.style_dict["font_color"] = self.style_dict.get("font_color_idle",
                                                            TextButton.DEFAULT_OPTIONS["font_color_idle"])
        self.style_dict["bg_color"] = self.style_dict.get("bg_color_idle", TextButton.DEFAULT_OPTIONS["bg_color_idle"])
        self.style_dict["theme"] = self.style_dict.get("theme_idle", TextButton.DEFAULT_OPTIONS["theme_idle"])
        label = Label(text=text,
                      position=position,
                      dimension=dimension,
                      style_dict=self.style_dict,
                      grow_width_with_text=grow_width_with_text,
                      grow_height_with_text=grow_height_with_text, multiline=multiline)
        self.image = self.idle_image = label.image

        random.setstate(state)  # To be sure to have the decoration on the same places...
        self.style_dict["font_color"] = self.style_dict.get("font_color_hover",
                                                            TextButton.DEFAULT_OPTIONS["font_color_hover"])
        self.style_dict["bg_color"] = self.style_dict.get("bg_color_hover",
                                                          TextButton.DEFAULT_OPTIONS["bg_color_hover"])
        self.style_dict["theme"] = self.style_dict.get("theme_hover", TextButton.DEFAULT_OPTIONS["theme_hover"])
        label = Label(text=text,
                      position=position,
                      dimension=dimension,
                      style_dict=self.style_dict,
                      grow_width_with_text=grow_width_with_text,
                      grow_height_with_text=grow_height_with_text, multiline=multiline)
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

    def move(self, dx, dy):
        self.rect.move_ip(dx, dy)


class ImageButton(Widget):
    """
    A button with an image
    """

    def __init__(self,
                 callback_function=None,
                 image=None,
                 image_hover=None,
                 position=(0, 0)):
        """

        :param callback_function: the function used as part of callback
        :param image: a surface that has the image that is displayed by default
        :param image_hover: None or the image that is displayed when the mouse is over the button
        :param position: the position for the widget
        """
        assert callback_function, "Button defined without callback function"

        Widget.__init__(self)

        self.callback_function = callback_function

        self.image = self.idle_image = image
        self.image_hover = image_hover or image

        self.rect = self.image.get_rect().move(position)
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
            self.image = self.image_hover
        else:
            self.image = self.idle_image

    def move(self, dx, dy):
        self.rect.move_ip(dx, dy)


class RadioButtonGroup(Widget):
    VERTICAL = "VERTICAL"
    HORIZONTAL = "HORIZONTAL"

    DEFAULT_OPTIONS = {
        "space_icon_label": 10,  # the space between the radiobutton and its label
        "space_between_components": 0,  # the space between components

        "theme": None,
        "bg_color": None,
        "extra_border_x": 5,  # if there is a theme or bg_color, the extra border horizontally
        "extra_border_y": 5
    }

    def __init__(self,
                 callback_function=None,
                 texts=None,
                 position=(0, 0),
                 image=None,
                 image_hover=None,
                 orientation=VERTICAL,
                 style_dict=None,
                 selected_index=0
                 ):

        assert callback_function, "Button defined without callback function"
        assert type(image) is pg.Surface, "Image needs to be a Surface"
        assert image_hover is None or type(image_hover) is pg.Surface, "Image hover needs to be a Surface"

        assert texts, "No text set"
        Widget.__init__(self)

        self.selected_index = selected_index
        self.callback_function = callback_function
        self.position = position
        self.orientation = orientation

        self.style_dict = style_dict or {}
        self.texts = texts
        self.theme = self.style_dict.get("theme", RadioButtonGroup.DEFAULT_OPTIONS["theme"])

        self.labels = [Label(text=str(text),
                             position=(0, 0),
                             grow_height_with_text=True,
                             grow_width_with_text=True,
                             style_dict={
                                 "text_margin_x": 0,
                                 "text_margin_y": 0,
                                 "theme": None,
                                 "bg_color": None,
                                 "font_name": self.style_dict.get("font_name", Label.DEFAULT_OPTIONS["font_name"]),
                                 "font_size": self.style_dict.get("font_name", Label.DEFAULT_OPTIONS["font_size"]),
                                 "font_color": self.style_dict.get("font_name", Label.DEFAULT_OPTIONS["font_color"]),
                             })
                       for text in texts]
        self.image_hover = image_hover or image
        self.image_idle = image

        self.max_label_width = max([label.rect.width for label in self.labels])
        self.max_label_height = max([label.rect.height for label in self.labels])
        margin = self.style_dict.get("space_icon_label", RadioButtonGroup.DEFAULT_OPTIONS["space_icon_label"])

        self.width_ref = self.max_label_width + max(self.image_idle.get_rect().width,
                                                    image_hover.get_rect().width) + margin
        self.height_ref = max(self.max_label_height,
                              self.image_idle.get_rect().height,
                              image_hover.get_rect().height) + self.style_dict.get("space_between_components",
                                                                                   RadioButtonGroup.DEFAULT_OPTIONS[
                                                                                       "space_between_components"])

        self.margin_x_left = self.margin_x_right = 0
        self.margin_y_top = self.margin_y_bottom = 0
        self._compute_margin()

        self.foreground_image = self.background_image = None
        self._create_foreground()
        self._create_background()

        self.image = self.background_image.copy()
        self.image.blit(self.foreground_image, (self.margin_x_left, self.margin_y_top))

        self.rect = self.image.get_rect()
        self.rect.move_ip(self.position)

    def _create_foreground(self):
        """
        Create the front part, i.e the parts containing the buttons and label
        :return:
        """
        if self.orientation == RadioButtonGroup.VERTICAL:
            self.foreground_image = pg.Surface((self.width_ref, self.height_ref * len(self.labels)), pg.SRCALPHA)

            # Blit the images
            for index, label in enumerate(self.labels):
                self.foreground_image.blit(label.image, (self.width_ref - self.max_label_width, self.height_ref * index))
                if index == self.selected_index:
                    self.foreground_image.blit(self.image_hover, (0, self.height_ref * index))
                else:
                    self.foreground_image.blit(self.image_idle, (0, self.height_ref * index))
        else:
            self.foreground_image = pg.Surface((self.width_ref * len(self.labels), self.height_ref), pg.SRCALPHA)
            # Blit the images
            for index, label in enumerate(self.labels):
                margin = self.style_dict.get("space_icon_label", RadioButtonGroup.DEFAULT_OPTIONS["space_icon_label"])

                self.foreground_image.blit(label.image,
                                           (self.width_ref * (index + 1) - self.max_label_width - int(margin / 2), 0))
                if index == self.selected_index:
                    self.foreground_image.blit(self.image_hover, (self.width_ref * index, 0))
                else:
                    self.foreground_image.blit(self.image_idle, (self.width_ref * index, 0))

    def _create_background(self):
        """
        Create the backround part, i.e the parts containing the buttons and label
        :return:
        """
        assert self.foreground_image, "Foreground image not computed before call to create background"
        foreground_rect = self.foreground_image.get_rect()
        self.background_image = pg.Surface((foreground_rect.width + self.margin_x_right + self.margin_x_left,
                                            foreground_rect.height + self.margin_y_bottom + self.margin_y_top),
                                           pg.SRCALPHA)

        # Blit the images
        bg_color = self.style_dict.get("bg_color", RadioButtonGroup.DEFAULT_OPTIONS["bg_color"])
        margin = 0  # Also used in decoration later

        if self.theme:
            rect = self.background_image.get_rect()
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

            elif self.theme["bg_color"]:
                # We just do something for the background
                self.background_image = rounded_surface(rect, self.theme["bg_color"],
                                                        radius=self.theme["rounded_angle"])
        elif bg_color:
            self.background_image.fill(bg_color)

    def _compute_margin(self):
        """
        Set margin_x left/right, and margin_y top/bottom
        :return:
        """
        if self.theme:
            self.margin_x_left = self.margin_x_right = self.style_dict.get("extra_border_x",
                                                                           RadioButtonGroup.DEFAULT_OPTIONS[
                                                                               "extra_border_x"])
            self.margin_y_top = self.margin_y_bottom = self.style_dict.get("extra_border_y",
                                                                           RadioButtonGroup.DEFAULT_OPTIONS[
                                                                               "extra_border_y"])
            for border_info in self.theme["borders"]:
                self.margin_x_left += border_info[0]
                self.margin_x_right += border_info[0]
                self.margin_y_top += border_info[0]
                self.margin_y_bottom += border_info[0]
        elif "bg_color" in self.style_dict:
            self.margin_x_left = self.margin_x_right = self.style_dict.get("extra_border_x",
                                                                           RadioButtonGroup.DEFAULT_OPTIONS[
                                                                               "extra_border_x"])
            self.margin_y_top = self.margin_y_bottom = self.style_dict.get("extra_border_y",
                                                                           RadioButtonGroup.DEFAULT_OPTIONS[
                                                                               "extra_border_y"])

    def handle_event(self, event):
        if event.type == pg.MOUSEBUTTONDOWN and self.rect.collidepoint(event.pos):
            if self.orientation == RadioButtonGroup.VERTICAL:
                self.selected_index = int((event.pos[1] - self.rect.top - self.margin_y_top) / self.height_ref)
            else:
                self.selected_index = int((event.pos[0] - self.rect.left - self.margin_x_left) / self.width_ref)

            if self.selected_index < len(self.texts):
                self._create_foreground()
                self.image = self.background_image.copy()
                self.image.blit(self.foreground_image, (self.margin_x_left, self.margin_y_top))

                self.callback_function(self.texts[self.selected_index])


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
