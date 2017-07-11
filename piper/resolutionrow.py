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

    index_label = GtkTemplate.Child()
    title_label = GtkTemplate.Child()
    revealer = GtkTemplate.Child()
    scale = GtkTemplate.Child()
    default_check = GtkTemplate.Child()

    def __init__(self, ratbagd_resolution, *args, **kwargs):
        """Instantiates a new ResolutionRow.

        @param ratbagd_resolution The resolution to configure, as
                                  ratbagd.RatbagdResolution.
        """
        Gtk.ListBoxRow.__init__(self, *args, **kwargs)
        self.init_template()
        self._resolution = ratbagd_resolution
        self._resolution.connect("notify::is-default", self._on_is_default_changed)
        self._default_handler = self.default_check.connect("toggled",
                                                           self._on_default_toggled)
        self._resolution_handler = self._resolution.connect("notify::resolution",
                                                            self._on_resolution_changed)
        self._init_values()

    def _init_values(self):
        # Initializes the configuration widgets.
        xres, __ = self._resolution.resolution
        minres = self._resolution.minimum
        maxres = self._resolution.maximum

        self.index_label.set_text("Resolution {}".format(self._resolution.index))

        self.scale.props.adjustment.configure(xres, minres, maxres, 50, 50, 0)
        self.scale.set_value(xres)
        if self._resolution.is_default:
            # Freeze the toggled signal from firing while we set the initial values.
            with self.default_check.handler_block(self._default_handler):
                self.default_check.set_active(True)
            self.default_check.set_sensitive(False)

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
        with self._resolution.handler_block(self._resolution_handler):
            self._resolution.resolution = xres, xres
        self.title_label.set_text("{} DPI".format(xres))

    @GtkTemplate.Callback
    def _on_scroll_event(self, widget, event):
        # Prevent a scroll in the list to get caught by the scale
        GObject.signal_stop_emission_by_name(widget, "scroll-event")
        return False

    def _on_default_toggled(self, check):
        print("\nToggled on resolution", self._resolution.index)
        # The user toggled us; set ourselves as the default. The rest happens in
        # self._on_is_default_changed.
        if check.get_active():
            self._resolution.set_default()

    def _on_is_default_changed(self, resolution, pspec):
        print("notify::is-default on resolution", resolution.index, resolution.is_default)
        # A RatbagdResolution's IsDefault has changed, update the checkbox if it
        # concerns us.
        if resolution.is_default:
            print("  New default")
            self.default_check.set_sensitive(False)
        elif self.default_check.get_active():
            print("  Old default")
            self.default_check.set_sensitive(True)
            # Freeze the toggled signal from firing to prevent Piper from
            # toggling back to the old default.
            with self.default_check.handler_block(self._default_handler):
                self.default_check.set_active(False)

    def _on_resolution_changed(self, resolution, pspec):
        # RatbagdResolution's resolution has changed, update the scale.
        xres, __ = resolution.resolution
        self.scale.set_value(xres)

    def toggle_revealer(self):
        """Toggles the revealer to show or hide the configuration widgets."""
        reveal = not self.revealer.get_reveal_child()
        self.revealer.set_reveal_child(reveal)
