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

import gi
gi.require_version("Gtk", "3.0")
from gi.repository import GObject, Gtk


@GtkTemplate(ui="/org/freedesktop/Piper/ui/ResolutionRow.ui")
class ResolutionRow(Gtk.ListBoxRow):
    """A Gtk.ListBoxRow subclass containing the widgets to configure a
    resolution."""

    __gtype_name__ = "ResolutionRow"

    title_label = GtkTemplate.Child()
    revealer = GtkTemplate.Child()
    scale = GtkTemplate.Child()

    def __init__(self, device, resolution, *args, **kwargs):
        Gtk.ListBoxRow.__init__(self, *args, **kwargs)
        self.init_template()

        self._resolution = None
        self._handler = 0

        device.connect("active-profile-changed",
                       self._on_active_profile_changed, resolution.index)

        self._init_values(resolution)

    def _init_values(self, resolution):
        if self._handler > 0:
            self._resolution.disconnect(self._handler)
        self._resolution = resolution
        self._handler = resolution.connect("notify::resolution", self._on_resolution_changed)

        xres, __ = resolution.resolution
        minres = resolution.minimum
        maxres = resolution.maximum

        self.scale.props.adjustment.configure(xres, minres, maxres, 50, 50, 0)
        # TODO: this updates the resolution upon initialization and makes the
        # profile dirty; should be wrapped in a `with self.scale.handler_block()`.
        self.scale.set_value(xres)

    def _on_active_profile_changed(self, device, profile, index):
        resolution = profile.resolutions[index]
        self._init_values(resolution)

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

    def _on_resolution_changed(self, resolution, pspec):
        # RatbagdResolution's resolution has changed, update the scales.
        xres, __ = resolution.resolution
        # TODO: this updates the resolution upon initialization and makes the
        # profile dirty; should be wrapped in a `with self.scale.handler_block()`.
        self.scale.set_value(xres)

    def toggle_revealer(self):
        """Toggles the revealer to show or hide the configuration widgets."""
        reveal = not self.revealer.get_reveal_child()
        self.revealer.set_reveal_child(reveal)
