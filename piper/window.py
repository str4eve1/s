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
from gi.repository import Gdk, GLib, Gtk, Gio


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

        self._add_perspective(ErrorPerspective(), ratbag)
        if ratbag is None:
            self._present_error_perspective(_("Cannot connect to ratbagd"),
                                            _("Please make sure ratbagd is running"))
            return

        for perspective in [MousePerspective(), WelcomePerspective()]:
            self._add_perspective(perspective, ratbag)

        welcome_perspective = self._get_child("welcome_perspective")
        welcome_perspective.connect("device-selected", self._on_device_selected)

        ratbag.connect("device-added", self._on_device_added)
        ratbag.connect("device-removed", self._on_device_removed)

        if len(ratbag.devices) == 0:
            self._present_error_perspective(_("Cannot find any devices"),
                                            _("Please make sure your device is supported and plugged in"))
        elif len(ratbag.devices) == 1:
            self._present_mouse_perspective(ratbag.devices[0])
        else:
            self._present_welcome_perspective(ratbag.devices)

    def do_delete_event(self, event):
        for perspective in self.stack_perspectives.get_children():
            if not perspective.can_shutdown:
                dialog = Gtk.MessageDialog(self, Gtk.DialogFlags.MODAL,
                                           Gtk.MessageType.QUESTION,
                                           Gtk.ButtonsType.YES_NO,
                                           _("There are unapplied changes. Are you sure you want to quit?"))
                response = dialog.run()
                dialog.destroy()

                if response == Gtk.ResponseType.NO or response == Gtk.ResponseType.DELETE_EVENT:
                    return Gdk.EVENT_STOP
        return Gdk.EVENT_PROPAGATE

    def _on_device_added(self, ratbag, device):
        if len(ratbag.devices) == 1:
            # We went from 0 devices to 1 device; immediately configure it.
            self._present_mouse_perspective(device)
        elif self.stack_perspectives.get_visible_child_name() == "welcome_perspective":
            # We're in the welcome perspective; just add it to the list.
            welcome_perspective = self._get_child("welcome_perspective")
            welcome_perspective.add_device(device)
        else:
            # We're configuring another device; just notify the user.
            # TODO: show in-app notification?
            print("Device connected")

    def _on_device_removed(self, ratbag, device):
        mouse_perspective = self._get_child("mouse_perspective")

        if device is mouse_perspective.device:
            # The current device disconnected, which can only happen from the
            # mouse perspective as we'd otherwise be in the welcome screen with
            # more than one device remaining. Hence, we display the error
            # perspective.
            self._present_error_perspective(_("Your device disconnected!"),
                                            _("Please make sure your device is plugged in"))
        elif self.stack_perspectives.get_visible_child_name() == "welcome_perspective":
            # We're in the welcome screen; just remove it from the list. If
            # there is nothing left, display the error perspective.
            welcome_perspective = self._get_child("welcome_perspective")
            welcome_perspective.remove_device(device)
            if len(ratbag.devices) == 0:
                self._present_error_perspective(_("Cannot find any devices"),
                                                _("Please make sure your device is supported and plugged in"))
        else:
            # We're configuring another device; just notify the user.
            # TODO: show in-app notification?
            print("Device disconnected")

    def _add_perspective(self, perspective, ratbag):
        self.stack_perspectives.add_named(perspective, perspective.name)
        self.stack_titlebar.add_named(perspective.titlebar, perspective.name)
        if perspective.can_go_back:
            button_back = Gtk.Button.new_from_icon_name("go-previous-symbolic",
                                                        Gtk.IconSize.BUTTON)
            button_back.set_visible(len(ratbag.devices) > 1)
            button_back.connect("clicked", lambda button, ratbag:
                                self._present_welcome_perspective(ratbag.devices),
                                ratbag)
            ratbag.connect("notify::devices", lambda ratbag, pspec:
                           button_back.set_visible(len(ratbag.devices) > 1))
            perspective.titlebar.add(button_back)
            # Place the button first in the titlebar.
            perspective.titlebar.child_set_property(button_back, "position", 0)

    def _present_welcome_perspective(self, devices):
        # Present the welcome perspective for the user to select one of their
        # devices.
        welcome_perspective = self._get_child("welcome_perspective")
        welcome_perspective.set_devices(devices)

        self.stack_titlebar.set_visible_child_name(welcome_perspective.name)
        self.stack_perspectives.set_visible_child_name(welcome_perspective.name)

    def _present_mouse_perspective(self, device):
        # Present the mouse configuration perspective for the given device.
        try:
            mouse_perspective = self._get_child("mouse_perspective")
            mouse_perspective.set_device(device)

            self.stack_titlebar.set_visible_child_name(mouse_perspective.name)
            self.stack_perspectives.set_visible_child_name(mouse_perspective.name)
        except ValueError as e:
            self._present_error_perspective(_("Cannot display device SVG"), str(e))
        except GLib.Error as e:
            # Happens with the GetSvgFd() call when running against older
            # python. This can be removed when we've had the newer call out
            # for a while. The full error is printed to stderr by
            # ratbagd.py.
            if e.code == Gio.DBusError.UNKNOWN_METHOD:
                self._present_error_perspective(_("Newer version of ratbagd required"),
                                                _('Please update to the latest available version'))
            else:
                self._present_error_perspective(_("Unknown exception occurred"), e.message)

    def _present_error_perspective(self, message, detail):
        # Present the error perspective informing the user of any errors.
        error_perspective = self._get_child("error_perspective")
        error_perspective.set_message(message)
        error_perspective.set_detail(detail)

        self.stack_titlebar.set_visible_child_name(error_perspective.name)
        self.stack_perspectives.set_visible_child_name(error_perspective.name)

    def _on_device_selected(self, perspective, device):
        self._present_mouse_perspective(device)

    def _get_child(self, name):
        return self.stack_perspectives.get_child_by_name(name)
