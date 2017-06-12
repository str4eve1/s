# Copyright (C) 2017 Jente Hidskes <hjdskes@gmail.com>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.

import cairo
import os
import sys

import gi
gi.require_version("Gdk", "3.0")
gi.require_version("Gio", "2.0")
gi.require_version("Gtk", "3.0")
gi.require_version("Rsvg", "2.0")
from gi.repository import Gdk, Gio, GLib, GObject, Gtk, Rsvg

"""This module contains the MouseMap widget (and its helper class
MouseMapChild), which is central to the button and LED configuration stack
pages. The MouseMap widget draws the device SVG in the center and lays out a
bunch of child widgets relative to the leaders in the device SVG."""

class MouseMapChild:
    """A helper class to manage children and their properties."""

    def __init__(self, widget, is_left, svg_id):
        self._widget = widget
        self._is_left = is_left
        self._svg_id = svg_id
        self._svg_leader = svg_id + "-leader"

    @property
    def widget(self):
        """The widget belonging to this child."""
        return self._widget

    @property
    def svg_id(self):
        """The identifier of the SVG element with which this child's widget is
        paired."""
        return self._svg_id

    @property
    def svg_leader(self):
        """The identifier of the leader SVG element with which this child's
        widget is paired."""
        return self._svg_leader

    @property
    def is_left(self):
        """True iff this child's widget is allocated to the left of the SVG."""
        return self._is_left

class MouseMap(Gtk.Container):
    """A Gtk.Container subclass to draw a device SVG with child widgets that
    map to the SVG. The SVG should have objects with identifiers, whose value
    should also be set on a custom `id` property of any child added to this
    container. See https://github.com/libratbag/libratbag/blob/master/data/README.md
    and do_size_allocate for more information.
    """

    __gtype_name__ = "MouseMap"

    __gproperties__ = {
        "spacing": (int,
                    "spacing",
                    "The amount of space between children and the SVG leaders",
                     0, GLib.MAXINT, 0,
                     GObject.PARAM_READABLE),
    }

    def __init__(self, layer, ratbagd_device, spacing=10, *args, **kwargs):
        """Instantiates a new MouseMap.

        @param ratbag_device The device that should be mapped, as ratbagd.RatbagdDevice
        @param spacing The spacing between the SVG leaders and the children, as int
        @param layer The SVG layer whose leaders to draw.

        @raises GLib.Error when the SVG cannot be loaded.
        """
        if layer is None:
            raise AttributeError("Layer cannot be None")
        if ratbagd_device is None:
            raise AttributeError("Device cannot be None")

        Gtk.Container.__init__(self, *args, **kwargs)
        self.set_has_window(False)

        self.spacing = spacing
        self._layer = layer
        self._device = ratbagd_device
        self._children = []
        self._highlight_element = None
        self._left_child_offset = 0

        #if not os.path.isfile(ratbag_device.svg_path):
        #    stream = Gio.Resource.open_stream("/org/freedesktop/Piper/404.svg",
        #                                      Gio.ResourceLookupFlags.NONE)
        #    self._handle = Rsvg.Handle.new_from_stream(stream, None,
        #                                               Rsvg.HandleFlags.FLAGS_NONE,
        #                                               None)
        #else:
        #    self._handle = Rsvg.Handle.new_from_file(ratbag_device.svg_path)
        self._handle = Rsvg.Handle.new_from_file("/home/jente/code/src/github.com/libratbag/libratbag/data/logitech-g700.svg")

    def do_add(self, widget):
        """Not implemented, use `add(widget, svg_id)` instead."""
        pass

    def add(self, widget, svg_id):
        """Adds the given widget to the map, bound to the given SVG element
        identifier. If the element identifier or its leader is not found in the
        SVG, the widget is not added.

        @param widget The widget to add, as Gtk.Widget
        @param svg_id The identifier of the SVG element with which this widget
                      is to be paired, as str
        """
        if widget is None or svg_id is None or not self._handle.has_sub(svg_id):
            return
        ok, svg_geom = self._get_svg_sub_geometry(svg_id + "-leader")
        if not ok:
            return
        # TODO: better detection for left-aligned children
        child = MouseMapChild(widget, svg_geom.x <= 100, svg_id)
        self._children.append(child)
        widget.connect("enter-notify-event", self._on_enter, child)
        widget.connect("leave-notify-event", self._on_leave)
        widget.set_parent(self)

    def do_remove(self, widget):
        """Removes the given widget from the map.

        @param widget The widget to remove, as Gtk.Widget
        """
        if not widget is None:
            for child in self._children:
                if child.widget == widget:
                    self._children.remove(child)
                    child.widget.unparent()
                    break

    def do_child_type(self):
        """Indicates that this container accepts any GTK+ widget."""
        return Gtk.Widget.get_type()

    def do_forall(self, include_internals, callback, *parameters):
        """Invokes the given callback on each child, with the given parameters.

        @param include_internals Whether to run on internal children as well, as
                                 boolean. Ignored, as there are no internal
                                 children.
        @param callback The callback to call on each child, as Gtk.Callback
        @param parameters The parameters to pass to the callback, as object or None
        """
        if not callback is None:
            for child in self._children:
                callback(child.widget, *parameters)

    def do_get_request_mode(self):
        """Gets whether the container prefers a height-for-width or a
        width-for-height layout. We don't want to trade width for height or
        height for width so we return CONSTANT_SIZE."""
        return Gtk.SizeRequestMode.CONSTANT_SIZE

    def do_get_preferred_height(self):
        """Calculates the container's initial minimum and natural height. While
        this call is specific to width-for-height requests (that we requested
        not to get) we cannot be certain that our wishes are granted and hence
        we must implement this method as well. In any case, we just return the
        maximum of the SVG's height or the children's summed (minimum and
        natural) height, including the border width."""
        # TODO: account for children sticking out under or above the SVG, if
        # they exist.
        svg_height = self._handle.props.height
        children_height_min = 0
        children_height_nat = 0
        for child in self._children:
            child_min, child_nat = child.widget.get_preferred_height()
            children_height_min += child_min
            children_height_nat += child_nat
        height_min = max(svg_height, children_height_min) + 2 * self.props.border_width
        height_nat = max(svg_height, children_height_nat) + 2 * self.props.border_width
        return (height_min, height_nat)

    def do_get_preferred_width(self):
        """Calculates the container's initial minimum and natural width. While
        this call is specific to height-for-width requests (that we requested
        not to get) we cannot be certain that our wishes are granted and hence
        we must implement this method as well. In any case, we just return the
        SVG's width, including the maximum (minimum and natural) child width,
        border width and spacing."""
        svg_width = self._handle.props.width
        left_children_width = max((child.widget.get_preferred_width()[1] for
                child in self._children if child.is_left), default=0)
        right_children_width = max(child.widget.get_preferred_width()[1] for
                child in self._children if not child.is_left)

        width_nat = left_children_width + svg_width + self.spacing + right_children_width + 2 * self.props.border_width
        if left_children_width > 0:
            width_nat += self.spacing
            self._left_child_offset = left_children_width + self.spacing
        return (width_nat, width_nat)

    def do_get_preferred_height_for_width(self, width):
        """Returns this container's minimum and natural height if it would be
        given the specified width. While this call is specific to
        height-for-width requests (that we requested not to get) we cannot be
        certain that our wishes are granted and hence we must implement this
        method as well. Since we really want to be the same size always, we
        simply return do_get_preferred_height.

        @param width The given width, as int. Ignored.
        """
        return self.do_get_preferred_height()

    def do_get_preferred_width_for_height(self, height):
        """Returns this container's minimum and natural width if it would be
        given the specified height. While this call is specific to
        width-for-height requests (that we requested not to get) we cannot be
        certain that our wishes are granted and hence we must implement this
        method as well. Since we really want to be the same size always, we
        simply return do_get_preferred_width.

        @param height The given height, as int. Ignored.
        """
        return self.do_get_preferred_width()

    def do_size_allocate(self, allocation):
        """Assigns a size and position to the child widgets. Children may adjust
        the given allocation in the adjust_size_allocation virtual method.

        This method uses a custom property on the children to position them
        relative to their SVG counterparts. Children that you want to be
        positioned should have an `id` property set on them, with value the SVG
        identifier they should position themselves next to. Children without
        this property are skipped.

        @param allocation The position and size allocated to this container, as Gdk.Rectangle
        """
        self.set_allocation(allocation)
        svg_width = self._handle.props.width
        child_allocation = Gdk.Rectangle()

        for child in self._children:
            if not child.widget.get_visible():
                continue
            child_allocation.x = self.props.border_width
            if not child.is_left:
                child_allocation.x += self._left_child_offset + svg_width + self.spacing
            svg_geom = self._get_svg_sub_geometry(child.svg_leader)[1]
            nat_size = child.widget.get_preferred_size()[1]
            child_allocation.y = svg_geom.y - 0.5 * nat_size.height
            child_allocation.width = nat_size.width
            child_allocation.height = nat_size.height
            if not child.widget.get_has_window():
                child_allocation.x += allocation.x
                child_allocation.y += allocation.y
            child.widget.size_allocate(child_allocation)

    def do_draw(self, cr):
        """Draws the container to the given Cairo context. The top left corner
        of the widget will be drawn to the currently set origin point of the
        context. The container needs to propagate the draw signal to its
        children.

        @param cr The Cairo context to draw into, as cairo.Context
        """
        for child in self._children:
            self.propagate_draw(child.widget, cr)

        cr.translate(self.props.border_width + self._left_child_offset, self.props.border_width)
        color = self.get_style_context().get_color(Gtk.StateFlags.LINK)
        cr.set_source_rgba(color.red, color.green, color.blue, 0.5)

        self._handle.render_cairo_sub(cr, id="#Device")
        if self._highlight_element is not None:
            svg_surface = cr.get_target()
            highlight_surface = svg_surface.create_similar(cairo.Content.COLOR_ALPHA,
                                                           self._handle.props.width,
                                                           self._handle.props.height)
            highlight_context = cairo.Context(highlight_surface)
            self._handle.render_cairo_sub(highlight_context, self._highlight_element)
            cr.mask_surface(highlight_surface, 0, 0)
        self._handle.render_cairo_sub(cr, id=self._layer)

    def do_get_property(self, prop):
        """Gets a property value.

        @param prop The property to get, as GObject.ParamSpec
        """
        if prop.name == "spacing":
            return self.spacing
        else:
            raise AttributeError("Unknown property %s" % prop.name)

    def _on_enter(self, widget, event, child):
        """Highlights the element in the SVG to which the entered widget belongs.

        @param widget The widget that fired this signal, as Gtk.Widget
        @param event The Gdk.EventCrossing that triggered this signal.
        @param child The child whose widget fired this signal, as MouseMapChild.
        """
        self._highlight_element = child.svg_id
        self._redraw_svg_element(child.svg_id)

    def _on_leave(self, widget, event):
        """Restores the device SVG to its original state.

        @param widget The widget that fired this signal, as Gtk.Widget
        @param event The Gdk.EventCrossing that triggered this signal.
        """
        old_highlight = self._highlight_element
        self._highlight_element = None
        self._redraw_svg_element(old_highlight)

    def _get_svg_sub_geometry(self, svg_id):
        """Helper method to get an SVG element's x- and y-coordinates, width and
        height.

        @param svg_id The identifier of the SVG element whose geometry to get.
        @returns (bool, Gdk.Rectangle)
        """
        ret = Gdk.Rectangle()
        ok, svg_pos = self._handle.get_position_sub(svg_id)
        if not ok:
            print("Warning: cannot retrieve element's position:", svg_id, file=sys.stderr)
            return ok, ret
        ret.x = svg_pos.x
        ret.y = svg_pos.y

        ok, svg_dim = self._handle.get_dimensions_sub(svg_id)
        if not ok:
            print("Warning: cannot retrieve element's dimensions:", svg_id, file=sys.stderr)
            return ok, ret
        ret.width = svg_dim.width
        ret.height = svg_dim.height
        return ok, ret

    def _redraw_svg_element(self, svg_id):
        """Helper method to redraw an element of the SVG image. Attempts to
        redraw only the element (plus an offset), but will fall back to
        redrawing the complete SVG.

        @param svg_id The identifier of the SVG element to redraw.
        """
        x = self.props.border_width + self._left_child_offset
        y = self.props.border_width
        ok, svg_geom = self._get_svg_sub_geometry(svg_id)
        if not ok:
            svg_width = self._handle.props.width
            svg_height = self._handle.props.height
            self.queue_draw_area(x, y, svg_width, svg_height)
        else:
            self.queue_draw_area(x + svg_geom.x - 10, y + svg_geom.y - 10,
                                 svg_geom.width + 20, svg_geom.height + 20)
