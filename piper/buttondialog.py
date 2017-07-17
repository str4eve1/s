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

    def __init__(self, ratbagd_button, *args, **kwargs):
        """Instantiates a new ButtonDialog.

        @param ratbagd_button The button to configure, as ratbagd.RatbagdButton.
        """
        Gtk.Dialog.__init__(self, *args, **kwargs)
        self.init_template()
        self._button = ratbagd_button
        self._action_type = self._button.action_type

        self._init_ui()

    def _init_ui(self):
        action_types = self._button.action_types
        for action_type in action_types:
            page = self._BUTTON_TYPE_TO_PAGE[action_type]
            self.stack.get_child_by_name(page).set_visible(True)
            if self._action_type == action_type:
                self.stack.set_visible_child_name(page)

    @GObject.Property
    def action_type(self):
        return self._action_type
