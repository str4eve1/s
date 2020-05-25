# SPDX-License-Identifier: GPL-2.0-or-later

from gettext import gettext as _

from .leddialog import LedDialog
from .mousemap import MouseMap
from .optionbutton import OptionButton
from .ratbagd import RatbagdLed

import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk  # noqa


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
        self._sizegroup = Gtk.SizeGroup(mode=Gtk.SizeGroupMode.HORIZONTAL)

        self._set_profile(self._device.active_profile)
        self.show_all()

    def _set_profile(self, profile):
        self._profile = profile
        for led in profile.leds:
            mode = _(RatbagdLed.LED_DESCRIPTION[led.mode])
            button = OptionButton(mode)
            button.connect("clicked", self._on_button_clicked, led)
            led.connect("notify::mode", self._on_led_mode_changed, button)
            self._mousemap.add(button, "#led{}".format(led.index))
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
        mode = _(RatbagdLed.LED_DESCRIPTION[led.mode])
        button.set_label(mode)

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
            led.effect_duration = dialog.effect_duration
        dialog.destroy()
