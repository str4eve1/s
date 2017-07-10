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
from .ratbagd import RatbagdLed

import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gdk, GObject, Gtk


@GtkTemplate(ui="/org/freedesktop/Piper/ui/LedDialog.ui")
class LedDialog(Gtk.Dialog):
    """A Gtk.Dialog subclass to implement the dialog that shows the
    configuration options for the LED effects."""

    __gtype_name__ = "LedDialog"

    stack = GtkTemplate.Child()
    colorchooser = GtkTemplate.Child()
    colorbutton = GtkTemplate.Child()
    adjustment_brightness = GtkTemplate.Child()
    adjustment_effect_rate = GtkTemplate.Child()

    def __init__(self, ratbagd_led, *args, **kwargs):
        """Instantiates a new LedDialog.

        @param ratbagd_led The LED to configure, as ratbagd.RatbagdLed.
        """
        Gtk.Dialog.__init__(self, *args, **kwargs)
        self.init_template()
        self._led = ratbagd_led
        self._modes = {
            "solid": RatbagdLed.MODE_ON,
            "cycle": RatbagdLed.MODE_CYCLE,
            "breathing": RatbagdLed.MODE_BREATHING,
            "off": RatbagdLed.MODE_OFF
        }

        mode = self._led.mode
        for k, v in self._modes.items():
            if mode == v:
                self.stack.set_visible_child_name(k)
        rgba = self._get_led_color_as_rgba()
        self.colorchooser.set_rgba(rgba)
        self.colorbutton.set_rgba(rgba)
        self.adjustment_brightness.set_value(self._led.brightness)
        self.adjustment_effect_rate.set_value(self._led.effect_rate)

    def _get_led_color_as_rgba(self):
        # Helper function to convert ratbagd's 0-255 color range to a Gdk.RGBA
        # with a 0.0-1.0 color range.
        r, g, b = self._led.color
        return Gdk.RGBA(r / 255.0, g / 255.0, b / 255.0, 1.0)

    @GObject.Property
    def mode(self):
        visible_child = self.stack.get_visible_child_name()
        return self._modes[visible_child]

    @GObject.Property
    def color(self):
        if self.mode == RatbagdLed.MODE_ON:
            rgba = self.colorchooser.get_rgba()
        else:
            rgba = self.colorbutton.get_rgba()
        return (rgba.red * 255.0, rgba.green * 255.0, rgba.blue * 255.0)

    @GObject.Property
    def brightness(self):
        return self.adjustment_brightness.get_value()

    @GObject.Property
    def effect_rate(self):
        return self.adjustment_effect_rate.get_value()
