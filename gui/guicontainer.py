import pygame as pg


class Container:
    """
    A set of class to align the rects of the widget it contains.
    A widget can only be a part of one container - a check is done to remove it when adding it.
    """

    def __init__(self, widgets=None, widget=None, reorder=False):
        self.widgets = {}
        self.widget_id_order = []
        self.internal_id = 0
        if widget:
            self.add_widget(widget, reorder=reorder)
        if widgets:
            self.add_widgets(widgets, reorder=reorder)

    def add_widget(self, widget, widget_id=None, reorder=True):
        # remove the widget from a previous container:
        if widget.container_parent:
            widget.container_parent.remove_widget_by_id(widget)

        if not widget_id:
            widget_id = self.internal_id
            self.internal_id += 1

        self.widgets[widget_id] = widget
        self.widget_id_order.append(widget_id)
        widget.container_parent = self
        widget.id_in_container = widget_id

        if reorder:
            self.reorder_container()

    def add_widgets(self, widget_list, reorder=True):
        for widget in widget_list:
            self.add_widget(widget, reorder=reorder)

    def insert_widget_after(self, widget_to_insert, widget_reference, reorder=True):
        """
        Insert a widget just after the widget reference one. If the widget reference doesn't exist, add it at the end
        :param widget_to_insert: the widget to insert
        :param widget_reference: the widget after which it needs to be inserted
        :param reorder: if set to True will not trigger the reordering
        :return: Nothing
        """
        if widget_reference.id not in self.widget_id_order:
            self.add_widget(widget_to_insert, reorder=True)
        else:
            copy_order = self.widget_id_order[:]
            self.add_widget(widget_to_insert, reorder=True)
            self.widget_id_order = copy_order[:copy_order.index(widget_reference.id) + 1] + \
                                   [widget_to_insert.id] + \
                                   copy_order[copy_order.index(widget_reference.id) + 1:]
        if reorder:
            self.reorder_container()

    def insert_widget_before(self, widget_to_insert, widget_reference, reorder=True):
        """
        Insert a widget just after the widget reference one. If the widget reference doesn't exist, add it at the beginning
        :param widget_to_insert: the widget to insert
        :param widget_reference: the widget after which it needs to be inserted
        :return: Nothing
        """
        if widget_reference.id not in self.widget_id_order:
            copy_order = self.widget_id_order[:]
            self.add_widget(widget_to_insert, reorder=True)
            self.widget_id_order = [widget_to_insert.id] + copy_order
        else:
            copy_order = self.widget_id_order[:]
            self.add_widget(widget_to_insert, reorder=True)
            self.widget_id_order = copy_order[:copy_order.index(widget_reference.id)] + \
                                   [widget_to_insert.id] + \
                                   copy_order[copy_order.index(widget_reference.id):]
        if reorder:
            self.reorder_container()

    def remove_widget_by_id(self, widget, reorder=True):
        if widget is None or widget.id_in_container is None:
            return
        if widget.id_in_container in self.widgets.keys():
            self.widgets[widget.id_in_container].container_parent = None
            self.widgets[widget.id_in_container].id = None
            self.widgets.pop(widget.id_in_container)
            self.widget_id_order.remove(widget.id_in_container)
        if reorder:
            self.reorder_container()

    def remove_widget_by_id(self, widget_id, reorder=True):
        if widget_id in self.widgets.keys():
            self.widgets[widget_id].container_parent = None
            self.widgets[widget_id].id = None
            self.widgets.pop(widget_id)
            self.widget_id_order.remove(widget_id)
        if reorder:
            self.reorder_container()

    def remove_all_widgets(self):
        for widget_id in self.widgets.key():
            self.remove_widget_by_id(widget_id, reorder=False)
        self.internal_id = 0

    def reorder_container(self):
        pass

    def widgets_as_list(self):
        listing = []
        for widget in self.widgets.values():
            listing.append(widget)
        return listing

    @property
    def rect(self):
        """
        This computes the rect that encompasses all widget
        :return: The rect that encompasses all widgets
        """
        if len(self.widget_id_order) == 0:
            return pg.Rect((0, 0), (0, 0))
        width = self.widgets[self.widget_id_order[-1]].rect.right - self.widgets[self.widget_id_order[0]].rect.left
        height = self.widgets[self.widget_id_order[-1]].rect.bottom - self.widgets[self.widget_id_order[0]].rect.top
        return pg.Rect(self.widgets[self.widget_id_order[0]].rect.topleft,
                       (width, height))

    def move(self, dx, dy):
        """
        Move all the rects of the widgets
        :param dx: the delta x to move
        :param dy: the delta y to move
        :return:
        """
        for widget in self.widgets.values():
            # widget.rect.move_ip(dx, dy)
            widget.move(dx, dy)


class LineAlignedContainer(Container):
    """
    A container that will aligned all its widgets according to a virtual line.
    The widgets can be vertically aligned:
    * Vertical left means that all widgets left side will be glued
    * Vertical center means that all widgets will be centered according to the vertical line
    * Vertical right means that all the widgets right side will be aligned
    The widgets can be horizontally aligned
    * Horizontal top means that all widgets top side will be glued
    * Horizontal center means that all widgets will be centered according to the horizontal line
    * Horizontal bottom means that all the widgets bottom side will be aligned
    """

    VERTICAL_LEFT = "VERTICAL_LEFT"
    VERTICAL_CENTER = "VERTICAL_CENTER"
    VERTICAL_RIGHT = "VERTICAL_RIGHT"
    HORIZONTAL_TOP = "HORIZONTAL_TOP"
    HORIZONTAL_CENTER = "HORIZONTAL_CENTER"
    HORIZONTAL_BOTTOM = "HORIZONTAL_BOTTOM"

    def __init__(self,
                 start_position,
                 alignment=VERTICAL_LEFT,
                 end_position=None,
                 space=None,
                 auto_space=False,
                 widget=None,
                 widgets=None,
                 reorder=False):
        """
        Define a new line aligned container, potentially with pre-made widget(s)
        :param start_position: the start of the line. Can be a single coordinate
        (handled as x or y axis dependent on the alignment)
        :param alignment: one of the different alignment
        (vertical/horizontal, mixed with which side of the widget needs to be glued)
        :param end_position: optional end position. Only mandatory if auto_space is set.
        :param space: the space between the widgets. If auto space is set to True this is ignored
        :param auto_space: compute the space between widgets. Needs the end_position to be set.
        :param widget: a single widget to add as part of the init.
        :param widgets: a list of widgets to add as part of the init.
        :param reorder: if set to False (default), will automatically reorder the container at the end of the init.
        """
        Container.__init__(self, widget=widget, widgets=widgets, reorder=False)

        if auto_space:
            assert type(end_position) is tuple and type(start_position) is tuple, \
                "Auto space set but start position {} and end position {} are not tuple".format(start_position,
                                                                                                end_position)
        self.alignment = alignment
        self.start_position = start_position
        self.end_position = end_position
        self.space = space
        self.auto_space = auto_space

        if not reorder:
            self.reorder_container()

    def reorder_container(self):
        if self.alignment in [LineAlignedContainer.VERTICAL_LEFT,
                              LineAlignedContainer.VERTICAL_CENTER,
                              LineAlignedContainer.VERTICAL_RIGHT]:
            self._reorder_container_vertical()
        else:
            self._reorder_container_horizontal()

    def _reorder_container_vertical(self):
        start_y = space = None
        reposition_y_axis = False

        if self.auto_space:
            start_y = self.start_position[1]
            end_y = self.end_position[1]
            total_widget_height = 0
            for widget in self.widgets.values():
                total_widget_height += widget.rect.height
            space = max(0, int((end_y - start_y - total_widget_height) / len(self.widget_id_order)))
            reposition_y_axis = True
        elif self.space:
            if type(self.start_position) is tuple:
                start_y = self.start_position[1]
            else:
                start_y = self.widgets[self.widget_id_order[0]].rect.top
            space = self.space
            reposition_y_axis = True

        # Now that everything is ready we prepare the move
        if reposition_y_axis:
            for widget_id in self.widget_id_order:
                self.widgets[widget_id].move(0, start_y - self.widgets[widget_id].rect.top)
                # self.widgets[widget_id].rect.top = start_y
                start_y += self.widgets[widget_id].rect.height + space

        if self.alignment == LineAlignedContainer.VERTICAL_LEFT:
            position = self.start_position
            if type(position) is tuple:
                position = position[0]
            for widget_id in self.widget_id_order:
                self.widgets[widget_id].move(position - self.widgets[widget_id].rect.left, 0)
                # self.widgets[widget_id].rect.left = position
        elif self.alignment == LineAlignedContainer.VERTICAL_RIGHT:
            position = self.start_position
            if type(position) is tuple:
                position = position[0]
            for widget_id in self.widget_id_order:
                # widget.rect.right = position
                self.widgets[widget_id].move(position - self.widgets[widget_id].rect.right, 0)
        else:
            position = self.start_position
            if type(position) is tuple:
                position = position[0]
            for widget_id in self.widget_id_order:
                # widget.rect.centerx = position
                self.widgets[widget_id].move(position - self.widgets[widget_id].rect.centerx, 0)

    def _reorder_container_horizontal(self):
        start_x = space = None
        reposition_x_axis = False

        if self.auto_space:
            start_x = self.start_position[0]
            end_x = self.end_position[0]
            total_widget_width = 0
            for widget in self.widgets.values():
                total_widget_width += widget.rect.width
            space = max(0, int((end_x - start_x - total_widget_width) / len(self.widget_id_order)))
            reposition_x_axis = True
        elif self.space:
            if type(self.start_position) is tuple:
                start_x = self.start_position[0]
            else:
                start_x = self.widgets[self.widget_id_order[0]].rect.left
            space = self.space
            reposition_x_axis = True

        if reposition_x_axis:
            for widget_id in self.widget_id_order:
                self.widgets[widget_id].move(start_x - self.widgets[widget_id].rect.left, 0)
                start_x += self.widgets[widget_id].rect.width + space

        if self.alignment == LineAlignedContainer.HORIZONTAL_TOP:
            position = self.start_position
            if type(position) is tuple:
                position = position[1]
            for widget_id in self.widget_id_order:
                self.widgets[widget_id].move(0, position - self.widgets[widget_id].rect.top)
        elif self.alignment == LineAlignedContainer.HORIZONTAL_BOTTOM:
            position = self.start_position
            if type(position) is tuple:
                position = position[1]
            for widget_id in self.widget_id_order:
                self.widgets[widget_id].move(0, position - self.widgets[widget_id].rect.bottom)
        else:
            position = self.start_position
            if type(position) is tuple:
                position = position[1]
            for widget_id in self.widget_id_order:
                self.widgets[widget_id].move(0, position - self.widgets[widget_id].rect.centery)
