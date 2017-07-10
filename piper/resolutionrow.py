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

from .gi_composites import GtkTemplate
from .ratbagd import RatbagdResolution

import gi
gi.require_version("Gtk", "3.0")
from gi.repository import GObject, Gtk


@GtkTemplate(ui="/org/freedesktop/Piper/ui/ResolutionRow.ui")
class ResolutionRow(Gtk.ListBoxRow):
    """A Gtk.ListBoxRow subclass containing the widgets to configure a
    resolution."""

    __gtype_name__ = "ResolutionRow"

    index_label = GtkTemplate.Child()
    title_label = GtkTemplate.Child()
    revealer = GtkTemplate.Child()
    scale = GtkTemplate.Child()

    def __init__(self, ratbagd_resolution, *args, **kwargs):
        Gtk.ListBoxRow.__init__(self, *args, **kwargs)
        self.init_template()
        self._resolution = ratbagd_resolution
        self._separate_xy = RatbagdResolution.CAP_SEPARATE_XY_RESOLUTION in \
            ratbagd_resolution.capabilities
        self._handler = self._resolution.connect("notify::resolution",
                                                 self._on_resolution_changed)
        self._init_values()

    def _init_values(self):
        # Initializes the scales and the title label and sets the Y resolution
        # configuration visible if it's supported by the device.
        xres, _ = self._resolution.resolution
        minres = self._resolution.min_res
        maxres = self._resolution.max_res

        self.index_label.set_text("Resolution {}".format(self._resolution.index))

        self.scale.props.adjustment.configure(xres, minres, maxres, 50, 50, 0)
        self.scale.set_value(xres)

    @GtkTemplate.Callback
    def _on_change_value(self, scale, scroll, value):
        # Round the value resulting from a scroll event to the nearest multiple
        # of 50. This is to work around the Gtk.Scale not snapping to its
        # Gtk.Adjustment's step_increment.
        scale.set_value(int(value - (value % 50)))
        return True

    @GtkTemplate.Callback
    def _on_delete_button_clicked(self, button):
        print("TODO: RatbagdProfile needs a way to delete resolutions")

    @GtkTemplate.Callback
    def _on_value_changed(self, scale):
        # The scale has been moved, update RatbagdResolution's resolution and
        # the title label.
        xres = int(self.scale.get_value())

        # Freeze the notify::resolution signal from firing to prevent Piper from
        # ending up in an infinite update loop.
        with self._resolution.handler_block(self._handler):
            self._resolution.resolution = xres, xres
        self.title_label.set_text("{} DPI".format(xres))

    @GtkTemplate.Callback
    def _on_scroll_event(self, widget, event):
        # Prevent a scroll in the list to get caught by the scale
        GObject.signal_stop_emission_by_name(widget, "scroll-event")
        return False

    def _on_resolution_changed(self, obj, pspec):
        # RatbagdResolution's resolution has changed, update the scales.
        xres, _ = self._resolution.resolution
        self.scale.set_value(xres)

    def toggle_revealer(self):
        """Toggles the revealer to show or hide the configuration widgets."""
        reveal = not self.revealer.get_reveal_child()
        self.revealer.set_reveal_child(reveal)
