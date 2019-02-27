# Copyright (C) 2019 Red Hat, Inc
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

from gi.repository import Gio

import configparser


def get_svg(model):
    resource = Gio.resources_lookup_data('/org/freedesktop/Piper/svgs/svg-lookup.ini', Gio.ResourceLookupFlags.NONE)

    data = resource.get_data()
    config = configparser.ConfigParser()
    config.read_string(data.decode('utf-8'), source='svg-lookup.ini')
    assert config.sections()

    filename = 'fallback.svg'

    if model.startswith('usb:') or model.startswith('bluetooth:'):
        bus, vid, pid, version = model.split(':')
        # Where the version is 0 (virtually all devices) we drop it. This
        # way the DeviceMatch lines are less confusing.
        if int(version) == 0:
            usbid = ':'.join([bus, vid, pid])
        else:
            usbid = model

        for s in config.sections():
            matches = config[s]['DeviceMatch'].split(';')
            if usbid in matches:
                filename = config[s]['Svg']
                break

    resource = Gio.resources_lookup_data('/org/freedesktop/Piper/svgs/{}'.format(filename),
                                         Gio.ResourceLookupFlags.NONE)

    return resource.get_data()
