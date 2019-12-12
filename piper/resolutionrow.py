# SPDX-License-Identifier: GPL-2.0-or-later

from .gi_composites import GtkTemplate
from .ratbagd import RatbagdResolution

import gi
gi.require_version("Gtk", "3.0")
from gi.repository import GObject, Gtk  # noqa


@GtkTemplate(ui="/org/freedesktop/Piper/ui/ResolutionRow.ui")
class ResolutionRow(Gtk.ListBoxRow):
    """A Gtk.ListBoxRow subclass containing the widgets to configure a
    resolution."""

    __gtype_name__ = "ResolutionRow"

    dpi_label = GtkTemplate.Child()
    active_label = GtkTemplate.Child()
    revealer = GtkTemplate.Child()
    scale = GtkTemplate.Child()
    active_button = GtkTemplate.Child()
    disable_button = GtkTemplate.Child()

    CAP_SEPARATE_XY_RESOLUTION = False
    CAP_DISABLE = False

    def __init__(self, device, resolution, *args, **kwargs):
        Gtk.ListBoxRow.__init__(self, *args, **kwargs)
        self.init_template()

        self._resolution = None
        self._resolution_handler = 0
        self._active_handler = 0
        self._disabled_handler = 0
        self._scale_handler = self.scale.connect("value-changed",
                                                 self._on_scale_value_changed)
        self._disabled_button_handler = self.disable_button.connect("toggled",
                                                                    self._on_disable_button_toggled)

        device.connect("active-profile-changed",
                       self._on_active_profile_changed, resolution.index)

        self._init_values(resolution)

    def _init_values(self, resolution):
        if self._resolution_handler > 0:
            self._resolution.disconnect(self._resolution_handler)
        if self._active_handler > 0:
            self._resolution.disconnect(self._active_handler)
        if self._disabled_handler > 0:
            self._resolution.disconnect(self._disabled_handler)
        self._resolution = resolution
        self.resolutions = resolution.resolutions
        self._resolution_handler = resolution.connect("notify::resolution",
                                                      self._on_resolution_changed)
        self._active_handler = resolution.connect("notify::is-active",
                                                  self._on_status_changed)
        self._disabled_handler = resolution.connect("notify::is-disabled",
                                                    self._on_status_changed)

        # Get resolution capabilities and update internal values.
        if RatbagdResolution.CAP_SEPARATE_XY_RESOLUTION in resolution.capabilities:
            self.CAP_SEPARATE_XY_RESOLUTION = True
        if RatbagdResolution.CAP_DISABLE in resolution.capabilities:
            self.CAP_DISABLE = True

        # Set initial values for the UI.
        res = resolution.resolution[0]
        minres = resolution.resolutions[0]
        maxres = resolution.resolutions[-1]
        with self.scale.handler_block(self._scale_handler):
            self.scale.props.adjustment.configure(res, minres, maxres, 50, 50, 0)
            self.scale.set_value(res)
        if resolution.is_disabled:
            with self.disable_button.handler_block(self._disabled_button_handler):
                self.disable_button.set_active(True)
        self._on_status_changed(resolution, pspec=None)

    def _on_active_profile_changed(self, device, profile, index):
        resolution = profile.resolutions[index]
        self._init_values(resolution)

    @GtkTemplate.Callback
    def _on_change_value(self, scale, scroll, value):
        # Cursor-controlled slider may get out of the GtkAdjustment's range.
        value = min(max(self.resolutions[0], value), self.resolutions[-1])

        # Find the nearest permitted value to our Gtk.Scale value.
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
            scale.props.adjustment.set_step_increment(delta)
            scale.props.adjustment.set_page_increment(delta)

        return True

    @GtkTemplate.Callback
    def _on_disable_button_toggled(self, togglebutton):
        # The disable button has been toggled, update RatbagdResolution.
        self._resolution.set_disabled(togglebutton.get_active())

        # Update UI
        self._on_status_changed(self._resolution, pspec=None)

    @GtkTemplate.Callback
    def _on_active_button_clicked(self, togglebutton):
        # The set active button has been clicked, update RatbagdResolution.
        self._resolution.set_active()

    @GtkTemplate.Callback
    def _on_scroll_event(self, widget, event):
        # Prevent a scroll in the list to get caught by the scale.
        GObject.signal_stop_emission_by_name(widget, "scroll-event")
        return False

    def _on_scale_value_changed(self, scale):
        # The scale has been moved, update RatbagdResolution's resolution.
        res = int(scale.get_value())
        self._on_dpi_values_changed(res=res)

    def _on_resolution_changed(self, resolution, pspec):
        # RatbagdResolution's resolution has changed, re-initialize.
        self._init_values(resolution)

    def _on_status_changed(self, resolution, pspec):
        # The resolution's status changed, update UI.
        self._on_dpi_values_changed()
        if resolution.is_active:
            self.active_label.set_visible(True)
            self.active_button.set_sensitive(False)
            self.disable_button.set_sensitive(False)
        else:
            self.active_label.set_visible(False)
            self.active_button.set_sensitive(True)
            if self.CAP_DISABLE:
                with self.disable_button.handler_block(self._disabled_button_handler):
                    self.disable_button.set_sensitive(True)
                    if resolution.is_disabled:
                        self.disable_button.set_active(True)
                        self.active_button.set_sensitive(False)
                        self.dpi_label.set_sensitive(False)
                        self.scale.set_sensitive(False)
                    else:
                        self.disable_button.set_active(False)
                        self.dpi_label.set_sensitive(True)
                        self.scale.set_sensitive(True)

    def toggle_revealer(self):
        # Toggles the revealer to show or hide the configuration widgets.
        reveal = not self.revealer.get_reveal_child()
        self.revealer.set_reveal_child(reveal)

    def _on_dpi_values_changed(self, res=None):
        # Freeze the notify::resolution signal from firing and
        # update dpi label and resolution values.
        if res is None:
            res = self._resolution.resolution[0]
        if self.CAP_SEPARATE_XY_RESOLUTION:
            new_res = (res, res)
        else:
            new_res = (res, )
        self.dpi_label.set_text("{} DPI".format(res))

        # Only update new resolution if changed
        if (new_res != self._resolution.resolution):
            with self._resolution.handler_block(self._resolution_handler):
                self._resolution.resolution = new_res
