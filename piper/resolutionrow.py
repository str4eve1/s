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

import gi
gi.require_version("Gtk", "3.0")
from gi.repository import GObject, Gtk  # noqa


@Gtk.Template(resource_path="/org/freedesktop/Piper/ui/ResolutionRow.ui")
class ResolutionRow(Gtk.ListBoxRow):
    """A Gtk.ListBoxRow subclass containing the widgets to configure a
    resolution."""

    __gtype_name__ = "ResolutionRow"

    dpi_label = Gtk.Template.Child()
    active_label = Gtk.Template.Child()
    revealer = Gtk.Template.Child()
    scale = Gtk.Template.Child()

    def __init__(self, device, resolution, *args, **kwargs):
        Gtk.ListBoxRow.__init__(self, *args, **kwargs)
        self.init_template()

        self._resolution = None
        self._resolution_handler = 0
        self._active_handler = 0
        self._scale_handler = self.scale.connect("value-changed",
                                                 self._on_scale_value_changed)

        device.connect("active-profile-changed",
                       self._on_active_profile_changed, resolution.index)

        self._init_values(resolution)

    def _init_values(self, resolution):
        if self._resolution_handler > 0:
            self._resolution.disconnect(self._resolution_handler)
        if self._active_handler > 0:
            self._resolution.disconnect(self._active_handler)
        self._resolution = resolution
        self._resolution_handler = resolution.connect("notify::resolution",
                                                      self._on_resolution_changed)
        self._active_handler = resolution.connect("notify::is-active",
                                                  self._on_is_active_changed)

        xres = resolution.resolution[0]
        minres = resolution.resolutions[0]
        maxres = resolution.resolutions[-1]
        self.resolutions = resolution.resolutions
        self.dpi_label.set_text("{} DPI".format(xres))
        self.active_label.set_visible(resolution.is_active)

        with self.scale.handler_block(self._scale_handler):
            self.scale.props.adjustment.configure(xres, minres, maxres, 50, 50, 0)
            self.scale.set_value(xres)

    def _on_active_profile_changed(self, device, profile, index):
        resolution = profile.resolutions[index]
        self._init_values(resolution)

    @Gtk.Template.Callback
    def _on_change_value(self, scale, scroll, value):

        # Cursor-controlled slider may get out of the GtkAdjustment's range
        value = min(max(self.resolutions[0], value), self.resolutions[-1])

        # Find the nearest permitted value to our Gtk.Scale value
        lo = max([r for r in self.resolutions if r <= value])
        hi = min([r for r in self.resolutions if r >= value])

        if value - lo < hi - value:
            value = lo
        else:
            value = hi

        scale.set_value(value)

        # libratbag provides a fake-exponential range with the deltas
        # increasing as the resolution goes up. Make sure we set our
        # steps to the next available value.
        idx = self.resolutions.index(value)
        if idx < len(self.resolutions) - 1:
            delta = self.resolutions[idx + 1] - self.resolutions[idx]
            self.scale.props.adjustment.set_step_increment(delta)
            self.scale.props.adjustment.set_page_increment(delta)

        return True

    @Gtk.Template.Callback
    def _on_scroll_event(self, widget, event):
        # Prevent a scroll in the list to get caught by the scale
        GObject.signal_stop_emission_by_name(widget, "scroll-event")
        return False

    def _on_scale_value_changed(self, scale):
        # The scale has been moved, update RatbagdResolution's resolution and
        # the title label.
        xres = int(self.scale.get_value())

        # Freeze the notify::resolution signal from firing to prevent Piper from
        # ending up in an infinite update loop.
        with self._resolution.handler_block(self._resolution_handler):
            if len(self._resolution.resolution) == 1:
                self._resolution.resolution = (xres, )
            else:
                self._resolution.resolution = (xres, xres)
        self.dpi_label.set_text("{} DPI".format(xres))

    def _on_resolution_changed(self, resolution, pspec):
        # RatbagdResolution's resolution has changed, update the scales.
        xres = resolution.resolution[0]
        self.scale.set_value(xres)

    def _on_is_active_changed(self, resolution, pspec):
        # The active resolution changed; update the visibility of the label.
        self.active_label.set_visible(resolution.is_active)

    def toggle_revealer(self):
        """Toggles the revealer to show or hide the configuration widgets."""
        reveal = not self.revealer.get_reveal_child()
        self.revealer.set_reveal_child(reveal)
        if reveal:
            self._resolution.set_active()
