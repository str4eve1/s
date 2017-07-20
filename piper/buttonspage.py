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

from .buttondialog import ButtonDialog
from .mousemap import MouseMap
from .optionbutton import OptionButton
from .ratbagd import RatbagdButton

import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk


class ButtonsPage(Gtk.Box):
    """The second stack page, exposing the button configuration."""

    __gtype_name__ = "ButtonsPage"

    def __init__(self, ratbagd_device, *args, **kwargs):
        """Instantiates a new ButtonsPage.

        @param ratbag_device The ratbag device to configure, as
                             ratbagd.RatbagdDevice
        """
        Gtk.Box.__init__(self, *args, **kwargs)
        self._device = ratbagd_device
        self._init_ui()

    def _init_ui(self):
        profile = self._find_active_profile()

        mousemap = MouseMap("#Buttons", self._device, spacing=20, border_width=20)
        self.pack_start(mousemap, True, True, 0)

        sizegroup = Gtk.SizeGroup(Gtk.SizeGroupMode.HORIZONTAL)
        for ratbagd_button in profile.buttons:
            index = ratbagd_button.index
            # TODO: add the correct *mapping to the label
            button = OptionButton(_("Button {}").format(index))
            button.connect("clicked", self._on_button_clicked, ratbagd_button)
            mousemap.add(button, "#button{}".format(index))
            sizegroup.add_widget(button)

    def _on_button_clicked(self, button, ratbagd_button):
        # Presents the ButtonDialog to configure the mouse button corresponding
        # to the clicked button.
        buttons = self._find_active_profile().buttons
        dialog = ButtonDialog(ratbagd_button, buttons, transient_for=self.get_toplevel())
        dialog.connect("response", self._on_dialog_response, ratbagd_button)
        dialog.present()

    def _on_dialog_response(self, dialog, response, ratbagd_button):
        # The user either pressed cancel or apply. If it's apply, apply the
        # changes before closing the dialog, otherwise just close the dialog.
        if response == Gtk.ResponseType.APPLY:
            if dialog.action_type == RatbagdButton.ACTION_TYPE_BUTTON:
                ratbagd_button.mapping = dialog.button_mapping
            elif dialog.action_type == RatbagdButton.ACTION_TYPE_KEY:
                ratbagd_button.key = dialog.key_mapping
            elif dialog.action_type == RatbagdButton.ACTION_TYPE_SPECIAL:
                ratbagd_button.special = dialog.special_mapping
        dialog.destroy()

    def _find_active_profile(self):
        # Finds the active profile, which is guaranteed to exist.
        for profile in self._device.profiles:
            if profile.is_active:
                return profile
