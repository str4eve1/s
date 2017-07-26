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

from gettext import gettext as _

from .buttonspage import ButtonsPage
from .gi_composites import GtkTemplate
from .profilerow import ProfileRow
from .ratbagd import RatbagErrorCode, RatbagdDevice
from .resolutionspage import ResolutionsPage
from .ledspage import LedsPage

import gi
gi.require_version("Gtk", "3.0")
from gi.repository import GLib, Gtk


@GtkTemplate(ui="/org/freedesktop/Piper/ui/Window.ui")
class Window(Gtk.ApplicationWindow):
    """A Gtk.ApplicationWindow subclass to implement the main application
    window. This Window contains the overlay for the in-app notifications, the
    headerbar and the stack holding a ResolutionsPage, a ButtonsPage and a
    LedsPage."""

    __gtype_name__ = "Window"

    stack = GtkTemplate.Child()
    notification_commit = GtkTemplate.Child()
    listbox_profiles = GtkTemplate.Child()
    label_profile = GtkTemplate.Child()
    add_profile_button = GtkTemplate.Child()

    def __init__(self, ratbag, *args, **kwargs):
        """Instantiates a new Window.

        @param ratbag The ratbag instance to connect to, as ratbagd.Ratbag
        """
        Gtk.ApplicationWindow.__init__(self, *args, **kwargs)
        self.init_template()

        if ratbag is None:
            self._present_error_dialog("Cannot connect to ratbagd")
            return

        self._ratbag = ratbag
        self._device = self._fetch_ratbag_device()
        if self._device is None:
            self._present_error_dialog("No devices found")
            return

        self._setup_pages()
        self._setup_profiles()

    def _setup_pages(self):
        try:
            capabilities = self._device.capabilities
            if RatbagdDevice.CAP_RESOLUTION in capabilities:
                self.stack.add_titled(ResolutionsPage(self._device), "resolutions", _("Resolutions"))
            if RatbagdDevice.CAP_BUTTON in capabilities:
                self.stack.add_titled(ButtonsPage(self._device), "buttons", _("Buttons"))
            if RatbagdDevice.CAP_LED in capabilities:
                self.stack.add_titled(LedsPage(self._device), "leds", _("LEDs"))
        except ValueError as e:
            self._present_error_dialog(e)
        except GLib.Error as e:
            self._present_error_dialog(e.message)

    def _setup_profiles(self):
        active_profile = self._device.active_profile
        self.label_profile.set_label(_("Profile {}").format(active_profile.index + 1))

        # Find the first profile that is enabled. If there is none, disable the
        # add button.
        left = next((p for p in self._device.profiles if not p.enabled), None)
        self.add_profile_button.set_sensitive(left is not None)

        for profile in self._device.profiles:
            profile.connect("notify::enabled", self._on_profile_notify_enabled)
            row = ProfileRow(profile)
            self.listbox_profiles.insert(row, profile.index)
            if profile == active_profile:
                self.listbox_profiles.select_row(row)

    def _present_error_dialog(self, message):
        # Present an error dialog informing the user of any errors.
        # TODO: this should be something in the window, not a print
        print("Cannot create window: {}".format(message))

    def _fetch_ratbag_device(self):
        """Get the first ratbag device available. If there are multiple
        devices, an error message is printed and we default to the first
        one. Otherwise, an error is shown and we return None.
        """
        # TODO: replace with better implementation once we go for the welcome screen.
        if len(self._ratbag.devices) == 0:
            print("Could not find any devices. Do you have anything vaguely mouse-looking plugged in?")
            return None
        elif len(self._ratbag.devices) > 1:
            print("Ooops, can't deal with more than one device. My bad.")
            for d in self._ratbag.devices[1:]:
                print("Ignoring device {}".format(d.name))
        return self._ratbag.devices[0]

    def _hide_notification_commit(self):
        if self._notification_commit_timeout_id is not 0:
            GLib.Source.remove(self._notification_commit_timeout_id)
            self._notification_commit_timeout_id = 0
        self.notification_commit.set_reveal_child(False)

    def _show_notification_commit(self):
        self.notification_commit.set_reveal_child(True)
        self._notification_commit_timeout_id = GLib.timeout_add_seconds(5,
                                                                        self._on_notification_commit_timeout)

    def _on_notification_commit_timeout(self):
        self._hide_notification_commit()
        return False

    @GtkTemplate.Callback
    def _on_save_button_clicked(self, button):
        status = self._device.commit()
        if not status == RatbagErrorCode.RATBAG_SUCCESS:
            self._show_notification_commit()

    @GtkTemplate.Callback
    def _on_notification_commit_close_clicked(self, button):
        self._hide_notification_commit()

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

    def _find_active_profile(self):
        # Finds the active profile, which is guaranteed to be found.
        for profile in self._device.profiles:
            if profile.is_active:
                return profile
