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
from .ratbagd import RatbagdButton

import gi
gi.require_version("Gtk", "3.0")
from gi.repository import GObject, Gtk


@GtkTemplate(ui="/org/freedesktop/Piper/ui/ButtonDialog.ui")
class ButtonDialog(Gtk.Dialog):
    """A Gtk.Dialog subclass to implement the dialog that shows the
    configuration options for button mappings."""

    __gtype_name__ = "ButtonDialog"

    _BUTTON_TYPE_TO_PAGE = {
        RatbagdButton.ACTION_TYPE_BUTTON: "mapping",
        RatbagdButton.ACTION_TYPE_SPECIAL: "special",
        RatbagdButton.ACTION_TYPE_KEY: "mapping",
        RatbagdButton.ACTION_TYPE_MACRO: "macro",
    }

    stack = GtkTemplate.Child()
    combo_mapping = GtkTemplate.Child()

    def __init__(self, ratbagd_button, buttons, *args, **kwargs):
        """Instantiates a new ButtonDialog.

        @param ratbagd_button The button to configure, as ratbagd.RatbagdButton.
        @param buttons The buttons on this device, as [ratbagd.RatbagdButton].
        """
        Gtk.Dialog.__init__(self, *args, **kwargs)
        self.init_template()
        self._button = ratbagd_button
        self._action_type = self._button.action_type
        self._button_mapping = ratbagd_button.mapping

        self._init_mapping_page(buttons)
        self._activate_current_page()

    def _activate_current_page(self):
        action_types = self._button.action_types
        for action_type in action_types:
            page = self._BUTTON_TYPE_TO_PAGE[action_type]
            self.stack.get_child_by_name(page).set_visible(True)
            if self._action_type == action_type:
                self.stack.set_visible_child_name(page)

    def _init_mapping_page(self, buttons):
        # Initializes the mapping stack page. First adds the semantic
        # description of all buttons' logical button assignments to the combobox
        # (activating the current applied item, if any) and secondly it adds the
        # item that triggers a key map configuration.
        for button in buttons:
            key, name = self._get_button_key_and_name(button)
            self.combo_mapping.append(key, name)
            if self._button_mapping > 0 and button == self._button:
                self.combo_mapping.set_active_id(key)

    def _get_button_key_and_name(self, button):
        if button.index in RatbagdButton.BUTTON_DESCRIPTION:
            name = RatbagdButton.BUTTON_DESCRIPTION[button.index]
        else:
            name = _("Button {} click").format(button.index)
        return str(button.index + 1), name  # Logical buttons are 1-indexed.

    @GtkTemplate.Callback
    def _on_mapping_changed(self, combo):
        tree_iter = combo.get_active_iter()
        if tree_iter is None:
            return
        model = combo.get_model()
        mapping = int(model[tree_iter][1])
        if mapping != self._button_mapping:
            self._button_mapping = mapping

    @GObject.Property
    def action_type(self):
        return self._action_type

    @GObject.Property
    def button_mapping(self):
        return self._button_mapping
