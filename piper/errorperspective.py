# SPDX-License-Identifier: GPL-2.0-or-later

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
