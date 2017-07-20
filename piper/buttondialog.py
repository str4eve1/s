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

from gettext import gettext as _

from .gi_composites import GtkTemplate
from .ratbagd import RatbagdButton
from .keystroke import KeyStroke

import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gdk, GObject, Gtk


@GtkTemplate(ui="/org/freedesktop/Piper/ui/ButtonDialog.ui")
class ButtonDialog(Gtk.Dialog):
    """A Gtk.Dialog subclass to implement the dialog that shows the
    configuration options for button mappings."""

    __gtype_name__ = "ButtonDialog"

    _BUTTON_TYPE_TO_PAGE = {
        RatbagdButton.ACTION_TYPE_BUTTON: "mapping",
        RatbagdButton.ACTION_TYPE_SPECIAL: "special",
        RatbagdButton.ACTION_TYPE_KEY: "mapping",
        RatbagdButton.ACTION_TYPE_MACRO: "macro",
    }

    _MODIFIERS = [
        Gdk.KEY_Shift_L,
        Gdk.KEY_Shift_R,
        Gdk.KEY_Shift_Lock,
        Gdk.KEY_Hyper_L,
        Gdk.KEY_Hyper_R,
        Gdk.KEY_Meta_L,
        Gdk.KEY_Meta_R,
        Gdk.KEY_Control_L,
        Gdk.KEY_Control_R,
        Gdk.KEY_Super_L,
        Gdk.KEY_Super_R,
        Gdk.KEY_Alt_L,
        Gdk.KEY_Alt_R,
    ]

    stack = GtkTemplate.Child()
    combo_mapping = GtkTemplate.Child()
    stack_mapping = GtkTemplate.Child()
    label_keystroke = GtkTemplate.Child()
    label_preview = GtkTemplate.Child()
    combo_special = GtkTemplate.Child()

    def __init__(self, ratbagd_button, buttons, *args, **kwargs):
        """Instantiates a new ButtonDialog.

        @param ratbagd_button The button to configure, as ratbagd.RatbagdButton.
        @param buttons The buttons on this device, as [ratbagd.RatbagdButton].
        """
        Gtk.Dialog.__init__(self, *args, **kwargs)
        self.init_template()
        self._grab_pointer = None
        self._keystroke = KeyStroke()
        self._button = ratbagd_button
        self._action_type = self._button.action_type
        self._button_mapping = ratbagd_button.mapping
        self._key_mapping = ratbagd_button.key
        self._special_mapping = ratbagd_button.special

        self._init_mapping_page(buttons)
        self._init_special_page()
        self._activate_current_page()

    def _activate_current_page(self):
        action_types = self._button.action_types
        for action_type in action_types:
            page = self._BUTTON_TYPE_TO_PAGE[action_type]
            self.stack.get_child_by_name(page).set_visible(True)
            if self._action_type == action_type:
                self.stack.set_visible_child_name(page)

    def _init_mapping_page(self, buttons):
        # Initializes the mapping stack page. First adds the semantic
        # description of all buttons' logical button assignments to the combobox
        # (activating the current applied item, if any) and secondly it adds the
        # item that triggers a key map configuration.
        for button in buttons:
            key, name = self._get_button_key_and_name(button)
            self.combo_mapping.append(key, name)
            if self._button_mapping > 0 and button == self._button:
                self.combo_mapping.set_active_id(key)

        self._keystroke.connect("keystroke-set", self._on_keystroke_set)
        self._keystroke.connect("keystroke-cleared", self._on_keystroke_set)
        self._keystroke.bind_property("accelerator", self.label_keystroke, "accelerator")
        self._keystroke.bind_property("accelerator", self.label_preview, "accelerator")
        if self._button.type == RatbagdButton.ACTION_TYPE_KEY:
            keys = self._button.key
            self._keystroke.set_from_evdev(keys[0], keys[1:])

    def _init_special_page(self):
        if self._button.type == RatbagdButton.ACTION_TYPE_SPECIAL:
            self.combo_special.set_active_id(self._special_mapping)

    def _get_button_key_and_name(self, button):
        if button.index in RatbagdButton.BUTTON_DESCRIPTION:
            name = RatbagdButton.BUTTON_DESCRIPTION[button.index]
        else:
            name = _("Button {} click").format(button.index)
        return str(button.index + 1), name  # Logical buttons are 1-indexed.

    def _grab_seat(self):
        # Grabs the keyboard seat. Returns True on success, False on failure.
        # Gratefully copied from GNOME Control Center's keyboard panel.
        window = self.get_window()
        if window is None:
            return False
        display = window.get_display()
        seats = display.list_seats()
        if len(seats) == 0:
            return False
        device = seats[0].get_keyboard()
        if device is None:
            return False
        if device.get_source == Gdk.InputSource.KEYBOARD:
            pointer = device.get_associated_device()
            if pointer is None:
                return False
        else:
            pointer = device
        status = pointer.get_seat().grab(window, Gdk.SeatCapabilities.KEYBOARD,
                                         False, None, None, None, None)
        if status != Gdk.GrabStatus.SUCCESS:
            return False
        self._grab_pointer = pointer
        self.grab_add()
        return True

    def _release_grab(self):
        # Releases a previously grabbed keyboard seat, if any.
        if self._grab_pointer is None:
            return
        self._grab_pointer.get_seat().ungrab()
        self._grab_pointer = None
        self.grab_remove()

    def do_key_press_event(self, event):
        # Overrides Gtk.Widget's standard key press event callback, so we can
        # capture the pressed buttons in capture mode. Gratefully copied from
        # GNOME Control Center's keyboard panel.
        # Don't process key events when we're not in capture mode.
        if self.stack_mapping.get_visible_child_name() == "overview":
            return Gtk.Widget.do_key_press_event(self, event)

        # TODO: remove this workaround when libratbag removes its keycode
        # contraints. When that happens, we just cache all keypresses in the
        # order they arrive and set the keystroke upon Return.
        # GdkEventKey.is_modified isn't exposed through PyGObject (see
        # https://bugzilla.gnome.org/show_bug.cgi?id=752784), so we have to
        # approximate its behaviour ourselves. This selection is from Gtk's
        # default mod mask and should be fine for now for most use cases.
        event.is_modifier = event.keyval in self._MODIFIERS

        # We only want to bind keystrokes using the default modifiers, so that
        # our workaround above and the one in KeyStroke._update_accelerator()
        # work.
        event.state &= Gtk.accelerator_get_default_mod_mask()

        # Put shift back if it changed the case of the key, not otherwise.
        keyval_lower = Gdk.keyval_to_lower(event.keyval)
        if keyval_lower != event.keyval:
            event.state |= Gdk.ModifierType.SHIFT_MASK
            event.keyval = keyval_lower

        # Normalize tab.
        if event.keyval == Gdk.KEY_ISO_Left_Tab:
            event.keyval = Gdk.KEY_Tab

        # HACK: we don't want to use SysRq as a keybinding, but we do want
        # Al+Print, so we avoid translating Alt+Print to SysRq.
        if event.keyval == Gdk.KEY_Sys_Req and (event.state & Gdk.ModifierType.MOD1_MASK):
            event.keyval = Gdk.KEY_Print

        # Backspace clears the current keystroke.
        if not event.is_modifier and event.state == 0 and event.keyval == Gdk.KEY_BackSpace:
            self._keystroke.clear()
            return Gdk.EVENT_STOP

        # Anything else we process as a regular key event.
        self._keystroke.process_event(event)

        return Gdk.EVENT_STOP

    def _on_keystroke_set(self, keystroke):
        # A keystroke has been set or cleared; update accordingly.
        self._action_type = RatbagdButton.ACTION_TYPE_KEY
        self._key_mapping = self._keystroke.get_keys()
        self.stack_mapping.set_visible_child_name("overview")
        self._release_grab()

    @GtkTemplate.Callback
    def _on_mapping_changed(self, combo):
        tree_iter = combo.get_active_iter()
        if tree_iter is None:
            return
        model = combo.get_model()
        mapping = int(model[tree_iter][1])
        if mapping != self._button_mapping:
            self._button_mapping = mapping
            self._action_type = RatbagdButton.ACTION_TYPE_BUTTON

    @GtkTemplate.Callback
    def _on_special_changed(self, combo):
        tree_iter = combo.get_active_iter()
        if tree_iter is None:
            return
        model = combo.get_model()
        mapping = model[tree_iter][0]
        if mapping != self._special_mapping:
            self._special_mapping = mapping
            self._action_type = RatbagdButton.ACTION_TYPE_SPECIAL

    @GtkTemplate.Callback
    def _on_capture_keystroke_clicked(self, button):
        # Switches to the capture stack page and grabs the keyboard seat to
        # capture all key presses.
        self.stack_mapping.set_visible_child_name("capture")
        if self._grab_seat() is not True:
            print("Unable to grab keyboard, can't set keystroke", file=sys.stderr)
            self.stack_mapping.set_visible_child_name("overview")

    @GObject.Property
    def action_type(self):
        return self._action_type

    @GObject.Property
    def button_mapping(self):
        return self._button_mapping

    @GObject.Property
    def key_mapping(self):
        return self._key_mapping

    @GObject.Property
    def special_mapping(self):
        return self._special_mapping
