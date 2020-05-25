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


@Gtk.Template(resource_path="/org/freedesktop/Piper/ui/ProfileRow.ui")
class ProfileRow(Gtk.ListBoxRow):
    """A Gtk.ListBoxRow subclass containing the widgets to display a profile in
    the profile poper."""

    __gtype_name__ = "ProfileRow"

    title = Gtk.Template.Child()

    def __init__(self, profile, *args, **kwargs):
        Gtk.ListBoxRow.__init__(self, *args, **kwargs)
        self.init_template()
        self._profile = profile
        self._profile.connect("notify::enabled", self._on_profile_notify_enabled)

        name = profile.name
        if not name:
            name = 'Profile {}'.format(profile.index)

        self.title.set_text(name)
        self.show_all()
        self.set_visible(profile.enabled)

    def _on_profile_notify_enabled(self, profile, pspec):
        self.set_visible(profile.enabled)

    @Gtk.Template.Callback
    def _on_delete_button_clicked(self, button):
        self._profile.enabled = False

    def set_active(self):
        """Activates the profile paired with this row."""
        self._profile.set_active()

    @GObject.Property
    def name(self):
        return self.title.get_text()
