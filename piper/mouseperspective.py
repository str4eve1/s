# SPDX-License-Identifier: GPL-2.0-or-later

from gettext import gettext as _

from .buttonspage import ButtonsPage
from .gi_composites import GtkTemplate
from .profilerow import ProfileRow
from .resolutionspage import ResolutionsPage
from .ledspage import LedsPage

import gi
gi.require_version("Gtk", "3.0")
from gi.repository import GLib, GObject, Gtk  # noqa


@GtkTemplate(ui="/org/freedesktop/Piper/ui/MousePerspective.ui")
class MousePerspective(Gtk.Overlay):
    """The perspective to configure a mouse."""

    __gtype_name__ = "MousePerspective"

    _titlebar = GtkTemplate.Child()
    stack = GtkTemplate.Child()
    notification_error = GtkTemplate.Child()
    listbox_profiles = GtkTemplate.Child()
    label_profile = GtkTemplate.Child()
    add_profile_button = GtkTemplate.Child()
    button_commit = GtkTemplate.Child()
    button_profile = GtkTemplate.Child()

    def __init__(self, *args, **kwargs):
        """Instantiates a new MousePerspective."""
        Gtk.Overlay.__init__(self, *args, **kwargs)
        self.init_template()
        self._device = None
        self._notification_error_timeout_id = 0

    @GObject.Property
    def name(self):
        """The name of this perspective."""
        return "mouse_perspective"

    @GObject.Property
    def titlebar(self):
        """The titlebar to this perspective."""
        return self._titlebar

    @GObject.Property
    def can_go_back(self):
        """Whether this perspective wants a back button to be displayed in case
        there is more than one connected device."""
        return True

    @GObject.Property
    def can_shutdown(self):
        if self._device is None:
            return True

        """Whether this perspective can safely shutdown."""
        for profile in self._device.profiles:
            if profile.dirty:
                return False
        return True

    @GObject.Property
    def device(self):
        return self._device

    def set_device(self, device):
        self._device = device
        device.connect("resync", lambda _: self._show_notification_error())

        self.stack.foreach(Gtk.Widget.destroy)
        active_profile = device.active_profile
        if active_profile.resolutions:
            self.stack.add_titled(ResolutionsPage(device), "resolutions", _("Resolutions"))
        if active_profile.buttons:
            self.stack.add_titled(ButtonsPage(device), "buttons", _("Buttons"))
        if active_profile.leds:
            self.stack.add_titled(LedsPage(device), "leds", _("LEDs"))

        self.button_profile.set_visible(len(device.profiles) > 1)
        name = active_profile.name
        if not name:
            name = 'Profile {}'.format(active_profile.index)
        self.label_profile.set_label(name)
        self._on_profile_notify_dirty(active_profile, None)

        # Find the first profile that is enabled. If there is none, disable the
        # add button.
        left = next((p for p in device.profiles if not p.enabled), None)
        self.add_profile_button.set_visible(left is not None)

        self.listbox_profiles.foreach(Gtk.Widget.destroy)
        for profile in device.profiles:
            profile.connect("notify::enabled", self._on_profile_notify_enabled)
            profile.connect("notify::dirty", self._on_profile_notify_dirty)
            row = ProfileRow(profile)
            self.listbox_profiles.insert(row, profile.index)
            if profile is active_profile:
                self.listbox_profiles.select_row(row)

    def _hide_notification_error(self):
        if self._notification_error_timeout_id != 0:
            GLib.Source.remove(self._notification_error_timeout_id)
            self._notification_error_timeout_id = 0
        self.notification_error.set_reveal_child(False)

    def _show_notification_error(self):
        self.notification_error.set_reveal_child(True)
        self._notification_error_timeout_id = GLib.timeout_add_seconds(5,
                                                                       self._on_notification_error_timeout)

    def _on_notification_error_timeout(self):
        self._hide_notification_error()
        return False

    @GtkTemplate.Callback
    def _on_save_button_clicked(self, button):
        self._device.commit()

    @GtkTemplate.Callback
    def _on_notification_error_close_clicked(self, button):
        self._hide_notification_error()

    @GtkTemplate.Callback
    def _on_profile_row_activated(self, listbox, row):
        row.set_active()
        self.label_profile.set_label(row.name)

    @GtkTemplate.Callback
    def _on_add_profile_button_clicked(self, button):
        # Enable the first disabled profile we find.
        for profile in self._device.profiles:
            if profile.enabled:
                continue
            profile.enabled = True
            if profile == self._device.profiles[-1]:
                self.add_profile_button.set_sensitive(False)
            break

    def _on_profile_notify_enabled(self, profile, pspec):
        # We're only interested in the case where the last profile is disabled,
        # so that we can reset the sensitivity of the add button.
        if not profile.enabled and profile == self._device.profiles[-1]:
            self.add_profile_button.set_sensitive(True)

    def _on_profile_notify_dirty(self, profile, pspec):
        style_context = self.button_commit.get_style_context()
        if profile.dirty:
            style_context.add_class("suggested-action")
            self.button_commit.set_sensitive(True)
        else:
            # There is no way to make a single profile non-dirty, so this works
            # for now. Ideally, this should however check if there are any other
            # profiles on the device that are dirty.
            style_context.remove_class("suggested-action")
            self.button_commit.set_sensitive(False)
