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
from gi.repository import GObject, Gtk  # noqa


@Gtk.Template(resource_path="/org/freedesktop/Piper/ui/ErrorPerspective.ui")
class ErrorPerspective(Gtk.Box):
    """A perspective to present an error condition in a user-friendly manner."""

    __gtype_name__ = "ErrorPerspective"

    label_error = Gtk.Template.Child()
    label_detail = Gtk.Template.Child()
    _titlebar = Gtk.Template.Child()

    def __init__(self, message=None, *args, **kwargs):
        """Instantiates a new ErrorPerspective.

        @param message The error message to display, as str.
        """
        Gtk.Box.__init__(self, *args, **kwargs)
        #self.init_template()
        if message is not None:
            self.set_message(message)

    @GObject.Property
    def name(self):
        """The name of this perspective."""
        return "error_perspective"

    @GObject.Property
    def titlebar(self):
        """The titlebar to this perspective."""
        return self._titlebar

    @GObject.Property
    def can_go_back(self):
        """Whether this perspective wants a back button to be displayed in case
        there is more than one connected device."""
        return False

    @GObject.Property
    def can_shutdown(self):
        """Whether this perspective can safely shutdown."""
        return True

    def set_message(self, message):
        """Sets the error message.

        @param message The error message to display, as str.
        """
        self.label_error.set_label(message)

    def set_detail(self, detail):
        """Sets the detail message.

        @param message The detail message to display, as str.
        """
        self.label_detail.set_label(detail)

    @Gtk.Template.Callback
    def _on_quit_button_clicked(self, button):
        window = button.get_toplevel()
        window.destroy()
