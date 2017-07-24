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

import sys

from copy import deepcopy
from evdev import ecodes

from .ratbagd import RatbagdButton

import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gdk, GObject


# TODO: this file needs to be checked for its Wayland support.
class KeyStroke(GObject.Object):
    """The KeyStroke object represents a keyboard shortcut as pressed by the
    user in the key mapping's capture mode. Note that internally it uses
    keycodes as defined by linux/input.h, not Gdk."""

    # Gdk uses an offset of 8 from the keycodes defined in linux/input.h.
    _XORG_KEYCODE_OFFSET = 8

    __gsignals__ = {
        'keystroke-set': (GObject.SIGNAL_RUN_FIRST, None, ()),
    }

    def __init__(self, **kwargs):
        """Intantiates a new KeyStroke."""
        GObject.Object.__init__(self, **kwargs)
        self._macro = ""
        self._keys = []
        self._cur_keys = []

    @GObject.Property(type=str)
    def macro(self):
        """A string representation of the current keystroke."""
        return self._macro

    def process_event(self, event):
        """Processes the given key event to update the current keystroke.

        @param event The event to process, as Gdk.EventKey.
        """
        if event.state == 0:
            # Return accepts and caches the current keystroke.
            if event.keyval == Gdk.KEY_Return:
                self._cur_keys = deepcopy(self._keys)
                self.emit("keystroke-set")
                return
            # Escape cancels the editing and restores the cache.
            elif event.keyval == Gdk.KEY_Escape:
                self._keys = deepcopy(self._cur_keys)
                self._cur_keys = []
                self._update_macro()
                self.emit("keystroke-set")
                return

        if event.type == Gdk.EventType.KEY_PRESS:
            type = RatbagdButton.MACRO_KEY_PRESS
        elif event.type == Gdk.EventType.KEY_RELEASE:
            type = RatbagdButton.MACRO_KEY_RELEASE
        keycode = event.hardware_keycode - self._XORG_KEYCODE_OFFSET
        # Only append if the entry isn't identical to the last one, as we cannot
        # e.g. have two identical key presses in a row.
        if len(self._keys) == 0 or (type, keycode) != self._keys[-1]:
            self._keys.append((type, keycode))

        self._update_macro()

    def set_from_evdev(self, macro):
        """Converts the given macro in libratbag format to its Gdk keycodes and
        sets them as the current keystroke.

        @param macro The macro in libratbag format, as [(type, str)].
        """
        for (type, keycode) in macro:
            if type == RatbagdButton.MACRO_WAIT:
                print("Piper does not yet support timeouts", file=sys.stderr)
                continue
            if not self._XORG_KEYCODE_OFFSET <= keycode <= 255:
                print("Keycode is not within the valid range.", file=sys.stderr)
                continue
            # Only append if the entry isn't identical to the last one, as we
            # cannot e.g. have two identical key presses in a row.
            if len(self._keys) == 0 or (type, keycode) != self._keys[-1]:
                self._keys.append((type, keycode))
        self._cur_keys = deepcopy(self._keys)
        self._update_macro()

    def get_macro(self):
        """Returns a list of (type, keycode) tuples representing the current
        keystroke, ready to be used by libratbagd."""
        return self._keys

    def _update_macro(self):
        # Updates the macro property, so that any GObject bindings to
        # Gtk.ShortcutLabels' macro property are updated automatically.
        keys = []
        for (type, keycode) in self._keys:
            keyval = ecodes.KEY[keycode]
            if type == RatbagdButton.MACRO_KEY_PRESS:
                keys.append("+{}".format(keyval))
            elif type == RatbagdButton.MACRO_KEY_RELEASE:
                keys.append("-{}".format(keyval))
        self._macro = " ".join(keys)
        self.notify("macro")
