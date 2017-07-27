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
from .mousemap import MouseMap
from .ratbagd import RatbagErrorCode
from .resolutionrow import ResolutionRow

import gi
gi.require_version("Gtk", "3.0")
from gi.repository import GLib, Gtk


@GtkTemplate(ui="/org/freedesktop/Piper/window.ui")
class Window(Gtk.ApplicationWindow):
    """A Gtk.ApplicationWindow subclass to implement the main application
    window."""

    __gtype_name__ = "ApplicationWindow"

    stack = GtkTemplate.Child()
    rate_500 = GtkTemplate.Child()
    rate_1000 = GtkTemplate.Child()
    box_resolutions = GtkTemplate.Child()
    listbox = GtkTemplate.Child()
    add_resolution_row = GtkTemplate.Child()
    notification_commit = GtkTemplate.Child()

    def __init__(self, ratbag, *args, **kwargs):
        """Instantiates a new Window.

        @param ratbag The ratbag instance to connect to, as ratbagd.Ratbag
        """
        Gtk.ApplicationWindow.__init__(self, *args, **kwargs)
        self.init_template()

        self._ratbag = ratbag
        self._device = self._fetch_ratbag_device()
        self._notification_commit_timeout_id = 0

        self._setup_resolutions_page()

    def _setup_resolutions_page(self):
        # TODO: mousemap needs to show which button switches resolution
        mousemap = MouseMap("#Device", self._device, spacing=20, border_width=20)

        self.rate_500.connect("toggled", self._on_report_rate_toggled, 500)
        self.rate_500.set_active(profile.active_resolution.report_rate == 500)
        self.rate_1000.connect("toggled", self._on_report_rate_toggled, 1000)
        self.rate_1000.set_active(profile.active_resolution.report_rate == 1000)

        self.box_resolutions.pack_start(mousemap, True, True, 0)
        # Place the MouseMap on the left
        self.box_resolutions.reorder_child(mousemap, 0)

        for resolution in profile.resolutions:
            row = ResolutionRow(resolution)
            self.listbox.insert(row, resolution.index)

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

    def _on_report_rate_toggled(self, button, rate):
        profile = self._device.active_profile
        profile.active_resolution.report_rate = rate

    @GtkTemplate.Callback
    def _on_row_activated(self, listbox, row):
        if row is self.add_resolution_row:
            print("TODO: RatbagdProfile needs a way to add resolutions")
        elif row is not None:
            row.toggle_revealer()

    @GtkTemplate.Callback
    def _on_save_button_clicked(self, button):
        status = self._device.commit()
        if not status == RatbagErrorCode.RATBAG_SUCCESS:
            self._show_notification_commit()

    @GtkTemplate.Callback
    def _on_notification_commit_close_clicked(self, button):
        self._hide_notification_commit()
