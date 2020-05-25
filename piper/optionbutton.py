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

import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk  # noqa


@Gtk.Template(resource_path="/org/freedesktop/Piper/ui/OptionButton.ui")
class OptionButton(Gtk.Button):
    """A Gtk.Button subclass that displays a label, a separator and a cog."""

    __gtype_name__ = "OptionButton"

    label = Gtk.Template.Child()

    def __init__(self, label=None, *args, **kwargs):
        """Instantiates a new OptionButton.

        @param label The text to display.
        """
        Gtk.Button.__init__(self, *args, **kwargs)
        self.init_template()
        if label is not None:
            self.set_label(label)

    def set_label(self, label):
        """Set the text to display.

        @param label The new text to display, as str.
        """
        self.label.set_text(label)
