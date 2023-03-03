# SPDX-License-Identifier: GPL-2.0-or-later

from gettext import gettext as _

from .buttonspage import ButtonsPage
from .profilerow import ProfileRow
from .ratbagd import RatbagdDevice, RatbagdProfile
from .resolutionspage import ResolutionsPage
from .advancedpage import AdvancedPage
from .ledspage import LedsPage
from .util.gobject import connect_signal_with_weak_ref

import gi

gi.require_version("Gtk", "3.0")
from gi.repository import GLib, GObject, Gtk  # noqa


@Gtk.Template(resource_path="/org/freedesktop/Piper/ui/MousePerspective.ui")
class MousePerspective(Gtk.Overlay):
    """The perspective to configure a mouse."""

    __gtype_name__ = "MousePerspective"

    _titlebar = Gtk.Template.Child()
    stack = Gtk.Template.Child()
    notification_error = Gtk.Template.Child()
    listbox_profiles = Gtk.Template.Child()
    label_profile = Gtk.Template.Child()
    add_profile_button = Gtk.Template.Child()
    button_commit = Gtk.Template.Child()
    button_profile = Gtk.Template.Child()

    def __init__(self, *args, **kwargs):
        """Instantiates a new MousePerspective."""
        Gtk.Overlay.__init__(self, *args, **kwargs)
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
        return all(not profile.dirty for profile in self._device.profiles)

    @GObject.Property
    def device(self):
        return self._device

    def set_device(self, device):
        self._device = device
        connect_signal_with_weak_ref(
            self, device, "resync", lambda _: self._show_notification_error()
        )
        connect_signal_with_weak_ref(
            self,
            self._device,
            "active-profile-changed",
            self._on_active_profile_changed,
        )

        active_profile = device.active_profile
        self._set_profile(active_profile)

        self.button_profile.set_visible(len(device.profiles) > 1)
        name = active_profile.name
        if not name:
            name = f"Profile {active_profile.index}"
        self.label_profile.set_label(name)

        # Find the first profile that is enabled. If there is none, disable the
        # add button.
        left = next((p for p in device.profiles if p.disabled), None)
        self.add_profile_button.set_visible(left is not None)

        self.listbox_profiles.foreach(Gtk.Widget.destroy)
        for profile in device.profiles:
            connect_signal_with_weak_ref(
                self, profile, "notify::enabled", self._on_profile_notify_enabled
            )
            connect_signal_with_weak_ref(
                self, profile, "notify::dirty", self._on_profile_notify_dirty
            )
            row = ProfileRow(profile)
            self.listbox_profiles.insert(row, profile.index)
            if profile is active_profile:
                self.listbox_profiles.select_row(row)

    def _set_profile(self, profile: RatbagdProfile) -> None:
        self.stack.foreach(Gtk.Widget.destroy)
        if profile.resolutions:
            self.stack.add_titled(
                ResolutionsPage(self._device), "resolutions", _("Resolutions")
            )
        if profile.buttons:
            self.stack.add_titled(ButtonsPage(self._device), "buttons", _("Buttons"))
        if profile.leds:
            self.stack.add_titled(LedsPage(self._device), "leds", _("LEDs"))
        if profile.angle_snapping != -1 or profile.debounces:
            self.stack.add_titled(AdvancedPage(self._device), "advanced", _("Advanced"))

        self._on_profile_notify_dirty(profile, None)

    def _hide_notification_error(self):
        if self._notification_error_timeout_id != 0:
            GLib.Source.remove(self._notification_error_timeout_id)
            self._notification_error_timeout_id = 0
        self.notification_error.set_reveal_child(False)

    def _show_notification_error(self):
        self.notification_error.set_reveal_child(True)
        self._notification_error_timeout_id = GLib.timeout_add_seconds(
            5, self._on_notification_error_timeout
        )

    def _on_active_profile_changed(
        self, device: RatbagdDevice, profile: RatbagdProfile
    ) -> None:
        # TODO: preserve the active tab.
        self._set_profile(profile)

    def _on_notification_error_timeout(self):
        self._hide_notification_error()
        return False

    @Gtk.Template.Callback("_on_save_button_clicked")
    def _on_save_button_clicked(self, button):
        self._device.commit()

    @Gtk.Template.Callback("_on_notification_error_close_clicked")
    def _on_notification_error_close_clicked(self, button):
        self._hide_notification_error()

    @Gtk.Template.Callback("_on_profile_row_activated")
    def _on_profile_row_activated(self, listbox, row):
        row.set_active()
        self.label_profile.set_label(row.name)

    @Gtk.Template.Callback("_on_add_profile_button_clicked")
    def _on_add_profile_button_clicked(self, button):
        # Enable the first disabled profile we find.
        for profile in self._device.profiles:
            if not profile.disabled:
                continue
            profile.disabled = False
            if profile == self._device.profiles[-1]:
                self.add_profile_button.set_sensitive(False)
            break

    def _on_profile_notify_enabled(self, profile, pspec):
        # We're only interested in the case where the last profile is disabled,
        # so that we can reset the sensitivity of the add button.
        if profile.disabled and profile == self._device.profiles[-1]:
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
