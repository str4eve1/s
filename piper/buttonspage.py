# SPDX-License-Identifier: GPL-2.0-or-later

from gettext import gettext as _
from evdev import ecodes

from .buttondialog import ButtonDialog
from .mousemap import MouseMap
from .optionbutton import OptionButton
from .ratbagd import RatbagdButton, RatbagdMacro

import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk  # noqa


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
        self._sizegroup = Gtk.SizeGroup(mode=Gtk.SizeGroupMode.HORIZONTAL)

        self._set_profile(self._device.active_profile)
        self.show_all()

    def _set_profile(self, profile):
        self._profile = profile
        for ratbagd_button in profile.buttons:
            button = OptionButton()
            # Set the correct label in the option button.
            self._on_button_mapping_changed(ratbagd_button, None, button)
            button.connect("clicked", self._on_button_clicked, ratbagd_button)
            ratbagd_button.connect("notify::mapping",
                                   self._on_button_mapping_changed, button)
            ratbagd_button.connect("notify::special",
                                   self._on_button_mapping_changed, button)
            ratbagd_button.connect("notify::macro",
                                   self._on_button_mapping_changed, button)
            ratbagd_button.connect("notify::key",
                                   self._on_button_mapping_changed, button)
            ratbagd_button.connect("notify::action-type",
                                   self._on_button_mapping_changed, button)
            self._mousemap.add(button, "#button{}".format(ratbagd_button.index))
            self._sizegroup.add_widget(button)

    def _on_active_profile_changed(self, device, profile):
        # Disconnect the notify::action_type signal on the old profile's buttons.
        for button in self._profile.buttons:
            button.disconnect_by_func(self._on_button_mapping_changed)
        # Clear the MouseMap of any children.
        self._mousemap.foreach(Gtk.Widget.destroy)
        # Repopulate the MouseMap.
        self._set_profile(profile)

    def _on_button_mapping_changed(self, ratbagd_button, pspec, optionbutton):
        # Called when the button's action type changed, which means its
        # corresponding optionbutton has to be updated.
        action_type = ratbagd_button.action_type
        if action_type == RatbagdButton.ActionType.BUTTON:
            if ratbagd_button.mapping - 1 in RatbagdButton.BUTTON_DESCRIPTION:
                label = _(RatbagdButton.BUTTON_DESCRIPTION[ratbagd_button.mapping - 1])
            else:
                # Translators: the {} will be replaced with the button index, e.g.
                # "Button 1 click".
                label = _("Button {} click").format(ratbagd_button.mapping - 1)
        elif action_type == RatbagdButton.ActionType.SPECIAL:
            label = _(RatbagdButton.SPECIAL_DESCRIPTION[ratbagd_button.special])
        elif action_type == RatbagdButton.ActionType.MACRO:
            label = _("Macro: {}").format(str(ratbagd_button.macro))
        elif action_type == RatbagdButton.ActionType.KEY:
            label = _("Key: {}").format(ecodes.KEY[ratbagd_button.key][RatbagdMacro._PREFIX_LEN:])
        elif action_type == RatbagdButton.ActionType.NONE:
            # Translators: the button is turned disabled, e.g. off.
            label = _("Disabled")
        else:
            # Translators: the button has an unknown function.
            label = _("Unknown")
        optionbutton.set_label(label)

    def _on_button_clicked(self, button, ratbagd_button):
        # Presents the ButtonDialog to configure the mouse button corresponding
        # to the clicked button.
        buttons = self._find_active_profile().buttons
        device_type = self._device.device_type
        dialog = ButtonDialog(
            ratbagd_button,
            buttons,
            device_type,
            title=_("Configure button {}").format(ratbagd_button.index),
            use_header_bar=True,
            transient_for=self.get_toplevel(),
        )
        dialog.connect("response", self._on_dialog_response, ratbagd_button)
        dialog.present()

    def _on_dialog_response(self, dialog, response, ratbagd_button):
        # The user either pressed cancel or apply. If it's apply, apply the
        # changes before closing the dialog, otherwise just close the dialog.
        if response == Gtk.ResponseType.APPLY:
            if dialog.action_type == RatbagdButton.ActionType.BUTTON:
                if dialog.mapping in [ButtonDialog.LEFT_HANDED_MODE, ButtonDialog.RIGHT_HANDED_MODE]:
                    left = self._find_button_type(0)
                    right = self._find_button_type(1)
                    if left is None or right is None:
                        return
                    # Mappings are 1-indexed, so 1 is left mouse click and 2 is
                    # right mouse click.
                    if dialog.mapping == ButtonDialog.LEFT_HANDED_MODE:
                        left.mapping, right.mapping = 2, 1
                    elif dialog.mapping == ButtonDialog.RIGHT_HANDED_MODE:
                        left.mapping, right.mapping = 1, 2
                else:
                    ratbagd_button.mapping = dialog.mapping
            elif dialog.action_type == RatbagdButton.ActionType.MACRO:
                ratbagd_button.macro = dialog.mapping
            elif dialog.action_type == RatbagdButton.ActionType.KEY:
                ratbagd_button.key = dialog.mapping
            elif dialog.action_type == RatbagdButton.ActionType.SPECIAL:
                ratbagd_button.special = dialog.mapping
                lower = RatbagdButton.ActionSpecial.PROFILE_CYCLE_UP
                upper = RatbagdButton.ActionSpecial.PROFILE_DOWN
                if lower <= dialog.mapping <= upper:
                    index = ratbagd_button.index
                    for profile in self._device.profiles:
                        if profile is self._profile:
                            continue
                        profile.buttons[index].special = dialog.mapping
        dialog.destroy()

    def _find_active_profile(self):
        # Finds the active profile, which is guaranteed to exist.
        for profile in self._device.profiles:
            if profile.is_active:
                return profile

    def _find_button_type(self, button_type):
        for button in self._profile.buttons:
            if button.index == button_type:
                return button
        return None
