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

from .errorperspective import ErrorPerspective
from .gi_composites import GtkTemplate
from .mouseperspective import MousePerspective
from .welcomeperspective import WelcomePerspective

import gi
gi.require_version("Gtk", "3.0")
from gi.repository import GLib, Gtk


@GtkTemplate(ui="/org/freedesktop/Piper/ui/Window.ui")
class Window(Gtk.ApplicationWindow):
    """A Gtk.ApplicationWindow subclass to implement the main application
    window. This window displays the different perspectives (error, mouse and
    welcome) that each present their own behavior."""

    __gtype_name__ = "Window"

    stack_titlebar = GtkTemplate.Child()
    stack_perspectives = GtkTemplate.Child()

    def __init__(self, ratbag, *args, **kwargs):
        """Instantiates a new Window.

        @param ratbag The ratbag instance to connect to, as ratbagd.Ratbag
        """
        Gtk.ApplicationWindow.__init__(self, *args, **kwargs)
        self.init_template()

        perspectives = [ErrorPerspective(), MousePerspective(), WelcomePerspective()]
        for perspective in perspectives:
            self._add_perspective(perspective)
        welcome_perspective = self.stack_perspectives.get_child_by_name("welcome_perspective")
        welcome_perspective.connect("device-selected", self._on_device_selected)

        if ratbag is None:
            self._present_error_perspective(_("Cannot connect to ratbagd"),
                                            _("Please make sure it is running"))
        elif len(ratbag.devices) == 0:
            self._present_error_perspective(_("Cannot find any devices"),
                                            _("Please make sure it is supported and plugged in"))
        elif len(ratbag.devices) == 1:
            self._present_mouse_perspective(ratbag.devices[0])
        else:
            self._present_welcome_perspective(ratbag.devices)

    def _add_perspective(self, perspective):
        self.stack_perspectives.add_named(perspective, perspective.name)
        self.stack_titlebar.add_named(perspective.titlebar, perspective.name)

    def _present_welcome_perspective(self, devices):
        # Present the welcome perspective for the user to select one of their
        # devices.
        welcome_perspective = self.stack_perspectives.get_child_by_name("welcome_perspective")
        welcome_perspective.set_devices(devices)

        self.stack_titlebar.set_visible_child_name(welcome_perspective.name)
        self.stack_perspectives.set_visible_child_name(welcome_perspective.name)

    def _present_mouse_perspective(self, device):
        # Present the mouse configuration perspective for the given device.
        try:
            mouse_perspective = self.stack_perspectives.get_child_by_name("mouse_perspective")
            mouse_perspective.set_device(device)

            self.stack_titlebar.set_visible_child_name(mouse_perspective.name)
            self.stack_perspectives.set_visible_child_name(mouse_perspective.name)
        except ValueError as e:
            self._present_error_perspective(_("Cannot display device SVG"), e)
        except GLib.Error as e:
            self._present_error_perspective(_("Unknown exception occurred"), e.message)

    def _present_error_perspective(self, message, detail):
        # Present the error perspective informing the user of any errors.
        error_perspective = self.stack_perspectives.get_child_by_name("error_perspective")
        error_perspective.set_message(message)
        error_perspective.set_detail(detail)

        self.stack_titlebar.set_visible_child_name(error_perspective.name)
        self.stack_perspectives.set_visible_child_name(error_perspective.name)

    def _on_device_selected(self, perspective, device):
        self._present_mouse_perspective(device)
