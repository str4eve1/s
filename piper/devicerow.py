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

from piper.svg import get_svg

import sys

import gi
gi.require_version("Gtk", "3.0")
from gi.repository import GdkPixbuf, GObject, Gtk, Rsvg  # noqa


@Gtk.Template(resource_path="/org/freedesktop/Piper/ui/DeviceRow.ui")
class DeviceRow(Gtk.ListBoxRow):
    """A Gtk.ListBoxRow subclass to present devices in the welcome
    perspective."""

    __gtype_name__ = "DeviceRow"

    title = Gtk.Template.Child()
    image = Gtk.Template.Child()

    def __init__(self, device, *args, **kwargs):
        Gtk.ListBoxRow.__init__(self, *args, **kwargs)
        #self.init_template()
        self._device = device
        self.title.set_text(device.name)

        try:
            svg_bytes = get_svg(device.model)
            handle = Rsvg.Handle.new_from_data(svg_bytes)
            svg = handle.get_pixbuf_sub("#Device")
            handle.close()
            if svg is None:
                print("Device {}'s SVG is incompatible".format(device.name), file=sys.stderr)
            else:
                svg = svg.scale_simple(50, 50, GdkPixbuf.InterpType.BILINEAR)
                if svg is None:
                    print("Cannot resize device SVG", file=sys.stderr)
                else:
                    self.image.set_from_pixbuf(svg)
        except FileNotFoundError:
            print("Device {} has no image or its path is invalid".format(device.name), file=sys.stderr)

        self.show_all()

    @GObject.Property
    def device(self):
        return self._device
