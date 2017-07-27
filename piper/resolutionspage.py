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

from .gi_composites import GtkTemplate
from .mousemap import MouseMap
from .resolutionrow import ResolutionRow

import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk


@GtkTemplate(ui="/org/freedesktop/Piper/ui/ResolutionsPage.ui")
class ResolutionsPage(Gtk.Box):
    """The first stack page, exposing the resolution configuration with its
    report rate buttons and resolutions list."""

    __gtype_name__ = "ResolutionsPage"

    rate_500 = GtkTemplate.Child()
    rate_1000 = GtkTemplate.Child()
    listbox = GtkTemplate.Child()
    add_resolution_row = GtkTemplate.Child()

    def __init__(self, ratbagd_device, *args, **kwargs):
        """Instantiates a new ResolutionsPage.

        @param ratbag_device The ratbag device to configure, as
                             ratbagd.RatbagdDevice
        """
        Gtk.Box.__init__(self, *args, **kwargs)
        self.init_template()

        self._device = ratbagd_device
        self._notification_commit_timeout_id = 0
        self._last_activated_row = None

        self._init_ui()

    def _init_ui(self):
        profile = self._device.active_profile

        mousemap = MouseMap("#Buttons", self._device, spacing=20, border_width=20)
        self.pack_start(mousemap, True, True, 0)
        # Place the MouseMap on the left
        self.reorder_child(mousemap, 0)
        for button in profile.buttons:
            if button.action_type == "special" and button.special == "resolution-default":
                label = Gtk.Label(_("Switch resolution"))
                mousemap.add(label, "#button{}".format(button.index))

        self.rate_500.connect("toggled", self._on_report_rate_toggled, 500)
        self.rate_500.set_active(profile.active_resolution.report_rate == 500)
        self.rate_1000.connect("toggled", self._on_report_rate_toggled, 1000)
        self.rate_1000.set_active(profile.active_resolution.report_rate == 1000)

        for resolution in profile.resolutions:
            row = ResolutionRow(resolution)
            self.listbox.insert(row, resolution.index)

    def _on_report_rate_toggled(self, button, rate):
        profile = self._device.active_profile
        profile.active_resolution.report_rate = rate

    @GtkTemplate.Callback
    def _on_row_activated(self, listbox, row):
        if row is self._last_activated_row:
            self._last_activated_row = None
            row.toggle_revealer()
        else:
            if self._last_activated_row is not None:
                self._last_activated_row.toggle_revealer()

            if row is self.add_resolution_row:
                print("TODO: RatbagdProfile needs a way to add resolutions")
            else:
                self._last_activated_row = row
                row.toggle_revealer()
