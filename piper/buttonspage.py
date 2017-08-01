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
        self._device.connect("active-profile-changed",
                             self._on_active_profile_changed)
        self._profile = None

        self._mousemap = MouseMap("#Buttons", self._device, spacing=20, border_width=20)
        self.pack_start(self._mousemap, True, True, 0)
        self._sizegroup = Gtk.SizeGroup(Gtk.SizeGroupMode.HORIZONTAL)

        self._set_profile(self._device.active_profile)

    def _set_profile(self, profile):
        self._profile = profile
        for ratbagd_button in profile.buttons:
            button = OptionButton()
            # Set the correct label in the option button.
            self._on_ratbagd_button_action_type_changed(ratbagd_button, None, button)
            button.connect("clicked", self._on_button_clicked, ratbagd_button)
            ratbagd_button.connect("notify::action-type",
                                   self._on_ratbagd_button_action_type_changed, button)
            self._mousemap.add(button, "#button{}".format(ratbagd_button.index))
            self._sizegroup.add_widget(button)

    def _on_active_profile_changed(self, device, profile):
        # Disconnect the notify::action_type signal on the old profile's buttons.
        for button in self._profile.buttons:
            button.disconnect_by_func(self._on_ratbagd_button_action_type_changed)
        # Clear the MouseMap of any children.
        self._mousemap.foreach(Gtk.Widget.destroy)
        # Repopulate the MouseMap.
        self._set_profile(profile)

    def _on_ratbagd_button_action_type_changed(self, ratbagd_button, pspec, optionbutton):
        # Called when the button's action type changed, which means its
        # corresponding optionbutton has to be updated.
        action_type = ratbagd_button.action_type
        if action_type == RatbagdButton.ACTION_TYPE_BUTTON:
            if ratbagd_button.mapping - 1 in RatbagdButton.BUTTON_DESCRIPTION:
                label = RatbagdButton.BUTTON_DESCRIPTION[ratbagd_button.mapping - 1]
            else:
                label = _("Button {} click").format(ratbagd_button.mapping - 1)
        elif action_type == RatbagdButton.ACTION_TYPE_SPECIAL:
            label = RatbagdButton.SPECIAL_DESCRIPTION[ratbagd_button.special]
        elif action_type == RatbagdButton.ACTION_TYPE_MACRO:
            label = _("Macro: {}").format(ratbagd_button.macro)
        elif action_type == RatbagdButton.ACTION_TYPE_NONE:
            label = _("Disabled")
        else:
            label = _("Unknown")
        optionbutton.set_label(label)

    def _on_button_clicked(self, button, ratbagd_button):
        # Presents the ButtonDialog to configure the mouse button corresponding
        # to the clicked button.
        buttons = self._find_active_profile().buttons
        dialog = ButtonDialog(ratbagd_button, buttons,
                              title=_("Configure button {}").format(ratbagd_button.index),
                              use_header_bar=True,
                              transient_for=self.get_toplevel())
        dialog.connect("response", self._on_dialog_response, ratbagd_button)
        dialog.present()

    def _on_dialog_response(self, dialog, response, ratbagd_button):
        # The user either pressed cancel or apply. If it's apply, apply the
        # changes before closing the dialog, otherwise just close the dialog.
        if response == Gtk.ResponseType.APPLY:
            if dialog.action_type == RatbagdButton.ACTION_TYPE_BUTTON:
                ratbagd_button.mapping = dialog.mapping
            elif dialog.action_type == RatbagdButton.ACTION_TYPE_MACRO:
                ratbagd_button.macro = dialog.mapping
            elif dialog.action_type == RatbagdButton.ACTION_TYPE_SPECIAL:
                ratbagd_button.special = dialog.mapping
        dialog.destroy()

    def _find_active_profile(self):
        # Finds the active profile, which is guaranteed to exist.
        for profile in self._device.profiles:
            if profile.is_active:
                return profile
