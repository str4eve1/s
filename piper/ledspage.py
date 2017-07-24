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

from .leddialog import LedDialog
from .mousemap import MouseMap
from .optionbutton import OptionButton
from .ratbagd import RatbagdLed

import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk


class LedsPage(Gtk.Box):
    """The third stack page, exposing the LED configuration."""

    __gtype_name__ = "LedsPage"

    def __init__(self, ratbagd_device, *args, **kwargs):
        """Instantiates a new LedsPage.

        @param ratbag_device The ratbag device to configure, as
                             ratbagd.RatbagdDevice
        """
        Gtk.Box.__init__(self, *args, **kwargs)
        self._device = ratbagd_device
        self._init_ui()

    def _init_ui(self):
        profile = self._find_active_profile()

        mousemap = MouseMap("#Leds", self._device, spacing=20, border_width=20)
        self.pack_start(mousemap, True, True, 0)

        sizegroup = Gtk.SizeGroup(Gtk.SizeGroupMode.HORIZONTAL)
        for led in profile.leds:
            index = led.index
            mode = self._mode_to_string(led.mode)
            button = OptionButton("LED {}: {}".format(index, mode))
            button.connect("clicked", self._on_button_clicked, led)
            led.connect("notify::mode", self._on_led_mode_changed, button)
            mousemap.add(button, "#led{}".format(index))
            sizegroup.add_widget(button)

    def _find_active_profile(self):
        # Finds the active profile, which is guaranteed to be found.
        for profile in self._device.profiles:
            if profile.is_active:
                return profile

    def _on_led_mode_changed(self, led, pspec, button):
        mode = self._mode_to_string(led.mode)
        button.set_label("LED {}: {}".format(led.index, mode))

    def _on_button_clicked(self, button, led):
        # Presents the LedDialog to configure the LED corresponding to the
        # clicked button.
        dialog = LedDialog(led, transient_for=self.get_toplevel())
        dialog.connect("response", self._on_dialog_response, button, led)
        dialog.present()

    def _on_dialog_response(self, dialog, response, button, led):
        # The user either pressed cancel or apply. If it's apply, apply the
        # changes before closing the dialog, otherwise just close the dialog.
        if response == Gtk.ResponseType.APPLY:
            led.mode = dialog.mode
            led.color = dialog.color
            led.brightness = dialog.brightness
            led.effect_rate = dialog.effect_rate
        dialog.destroy()

    def _mode_to_string(self, mode):
        # Converts a RatbagdLed mode to a string.
        if mode == RatbagdLed.MODE_ON:
            return _("solid")
        elif mode == RatbagdLed.MODE_CYCLE:
            return _("cycle")
        elif mode == RatbagdLed.MODE_BREATHING:
            return _("breathing")
        elif mode == RatbagdLed.MODE_OFF:
            return _("off")
        else:
            return _("n/a")
