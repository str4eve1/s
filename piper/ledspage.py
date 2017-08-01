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
        self._device.connect("active-profile-changed",
                             self._on_active_profile_changed)
        self._profile = None

        self._mousemap = MouseMap("#Leds", self._device, spacing=20, border_width=20)
        self.pack_start(self._mousemap, True, True, 0)
        self._sizegroup = Gtk.SizeGroup(Gtk.SizeGroupMode.HORIZONTAL)

        self._set_profile(self._device.active_profile)

    def _set_profile(self, profile):
        self._profile = profile
        for led in profile.leds:
            index = led.index
            mode = self._mode_to_string(led.mode)
            button = OptionButton("LED {}: {}".format(index, mode))
            button.connect("clicked", self._on_button_clicked, led)
            led.connect("notify::mode", self._on_led_mode_changed, button)
            self._mousemap.add(button, "#led{}".format(index))
            self._sizegroup.add_widget(button)

    def _on_active_profile_changed(self, device, profile):
        # Disconnect the notify::mode signal on the old profile's LEDs.
        for led in self._profile.leds:
            led.disconnect_by_func(self._on_led_mode_changed)
        # Clear the MouseMap of any children.
        self._mousemap.foreach(Gtk.Widget.destroy)
        # Repopulate the MouseMap.
        self._set_profile(profile)

    def _on_led_mode_changed(self, led, pspec, button):
        mode = self._mode_to_string(led.mode)
        button.set_label("LED {}: {}".format(led.index, mode))

    def _on_button_clicked(self, button, led):
        # Presents the LedDialog to configure the LED corresponding to the
        # clicked button.
        dialog = LedDialog(led, transient_for=self.get_toplevel())
        dialog.connect("response", self._on_dialog_response, led)
        dialog.present()

    def _on_dialog_response(self, dialog, response, led):
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
