# SPDX-License-Identifier: GPL-2.0-or-later

import gi
gi.require_version('Handy', '1')

from gi.repository import Gio, Handy  # noqa

import configparser


def get_svg(model):
    resource = Gio.resources_lookup_data('/org/freedesktop/Piper/svgs/svg-lookup.ini', Gio.ResourceLookupFlags.NONE)

    data = resource.get_data()
    config = configparser.ConfigParser()
    config.read_string(data.decode('utf-8'), source='svg-lookup.ini')
    assert config.sections()

    filename = 'fallback'

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

        if manager := Handy.StyleManager.get_default():
            if manager.get_dark():
                filename += '-dark'

    resource = Gio.resources_lookup_data('/org/freedesktop/Piper/svgs/{}.svg'.format(filename),
                                         Gio.ResourceLookupFlags.NONE)

    return resource.get_data()
