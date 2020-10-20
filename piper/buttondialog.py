# SPDX-License-Identifier: GPL-2.0-or-later

import sys

from gettext import gettext as _

from .gi_composites import GtkTemplate
from .ratbagd import RatbagdButton, RatbagdMacro

import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gdk, GObject, Gtk  # noqa


@GtkTemplate(ui="/org/freedesktop/Piper/ui/ButtonRow.ui")
class ButtonRow(Gtk.ListBoxRow):
    """A Gtk.ListBoxRow subclass to implement the rows that show up in the
    ButtonDialog's Gtk.ListBox. It doesn't do much besides moving UI code into a
    .ui file."""

    __gtype_name__ = "ButtonRow"

    description_label = GtkTemplate.Child()

    def __init__(self, description, section, action_type, value, *args, **kwargs):
        """Instantiates a new ButtonRow.

        @param description The text to display in the row, as str.
        @param section The section this row belongs to, as str.
        @param action_type The type of this row's mapping, as one of
                           RatbagdButton.ActionType.*.
        @param value The value to set when this row is activated. The type needs
                     to match the action_type, e.g. for it should be int for
                     RatbagdButton.ActionType.BUTTON.
        """
        Gtk.ListBoxRow.__init__(self, *args, **kwargs)
        self._section = section
        self._action_type = action_type
        self._value = value

        self.init_template()
        self.description_label.set_text(description)

    @GObject.Property
    def description(self):
        return self.description_label.get_text()


@GtkTemplate(ui="/org/freedesktop/Piper/ui/ButtonDialog.ui")
class ButtonDialog(Gtk.Dialog):
    """A Gtk.Dialog subclass to implement the dialog that shows the
    configuration options for button mappings."""

    __gtype_name__ = "ButtonDialog"

    LEFT_HANDED_MODE = -1000
    RIGHT_HANDED_MODE = -1001

    # Gdk uses an offset of 8 from the keycodes defined in linux/input.h.
    _XORG_KEYCODE_OFFSET = 8

    stack = GtkTemplate.Child()
    listbox = GtkTemplate.Child()
    label_keystroke = GtkTemplate.Child()
    label_preview = GtkTemplate.Child()
    row_keystroke = GtkTemplate.Child()
    row_keystroke_label = GtkTemplate.Child()
    radio_right_handed = GtkTemplate.Child()
    radio_left_handed = GtkTemplate.Child()
    empty_search_placeholder = GtkTemplate.Child()
    search_entry = GtkTemplate.Child()
    search_bar = GtkTemplate.Child()

    def __init__(self, ratbagd_button, buttons, *args, **kwargs):
        """Instantiates a new ButtonDialog.

        @param ratbagd_button The button to configure, as ratbagd.RatbagdButton.
        @param buttons The buttons on this device, as [ratbagd.RatbagdButton].
        """
        Gtk.Dialog.__init__(self, *args, **kwargs)
        self.init_template()
        self._grab_pointer = None
        self._current_macro = None
        self._button = ratbagd_button
        self._action_type = self._button.action_type
        if self._action_type == RatbagdButton.ActionType.BUTTON:
            self._mapping = self._button.mapping
        elif self._action_type == RatbagdButton.ActionType.MACRO:
            self._mapping = self._button.macro
        elif self._action_type == RatbagdButton.ActionType.SPECIAL:
            self._mapping = self._button.special
        else:
            self._mapping = -1

        self._init_ui(buttons)

    def _init_ui(self, buttons):
        if self._button.index in [0, 1]:
            self._init_primary_buttons_ui()
        else:
            self._init_other_buttons_ui(buttons)

    def _init_primary_buttons_ui(self):
        # Shows the listbox to swap the primary buttons.
        self.stack.set_visible_child_name("handedness")
        # Left mouse button (index 0) is mapped to right mouse button, where
        # mappings are 1-indexed and thus right mouse click has value 2.
        # Or, right mouse button (index 1) is mapped to left mouse button,
        # which has value 1.
        if self._button.index == 0 and self._mapping == 2 or \
                self._button.index == 1 and self._mapping == 1:
            self.radio_left_handed.set_active(True)
        else:
            self.radio_right_handed.set_active(True)

    def _init_other_buttons_ui(self, buttons):
        # Shows the listbox to map non-primary buttons.
        self.listbox.set_header_func(self._listbox_header_func)
        self.listbox.set_filter_func(self._listbox_filter_func)
        self.listbox.set_placeholder(self.empty_search_placeholder)
        self.search_entry.connect("notify::text", lambda o, p: self.listbox.invalidate_filter())

        i = 0
        for button in buttons:
            key, name = self._get_button_name_and_description(button)
            # Translators: section header for mapping one button's click to another.
            row = ButtonRow(name, _("Button mapping"), RatbagdButton.ActionType.BUTTON, button.index + 1)
            self.listbox.insert(row, i)
            if self._action_type == RatbagdButton.ActionType.BUTTON and button.index + 1 == self._button.mapping:
                self.listbox.select_row(row)
            i += 1
        for key, name in RatbagdButton.SPECIAL_DESCRIPTION.items():
            if name == "Unknown" or name == "Invalid":
                continue
            # Translators: section header for assigning special functions to buttons.
            row = ButtonRow(_(name), _("Special mapping"), RatbagdButton.ActionType.SPECIAL, key)
            self.listbox.insert(row, i)
            if self._action_type == RatbagdButton.ActionType.SPECIAL and key == self._mapping:
                self.listbox.select_row(row)
            i += 1

        if self._action_type == RatbagdButton.ActionType.MACRO:
            self._create_current_macro(macro=self._mapping)
        else:
            self._create_current_macro()

    def _create_current_macro(self, macro=None):
        if macro is not None:
            self._current_macro = macro
            self._on_macro_updated(macro, None)
        else:
            self._current_macro = RatbagdMacro()
        self._current_macro.connect("macro-set", self._on_macro_set)
        self._current_macro.connect("notify::keys", self._on_macro_updated)

    def _listbox_header_func(self, row, before):
        # Adds headers to those rows where a new category starts, to separate
        # different kinds of mappings.
        if row == self.row_keystroke:
            separator = Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL,
                                      margin_top=18)
            row.set_header(separator)
            return

        if before is not None:
            add_header = (row._section != before._section)
        else:
            add_header = True

        if not add_header:
            row.set_header(None)
            return

        box = Gtk.Box.new(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        if before is not None:
            box.set_margin_top(18)
        else:
            box.set_margin_top(6)

        markup = "<b>{}</b>".format(row._section)
        label = Gtk.Label(label=markup, use_markup=True, xalign=0.0, margin_start=6)
        label.get_style_context().add_class("dim-label")

        box.add(label)
        box.add(Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL))
        row.set_header(box)
        box.show_all()

    def _listbox_filter_func(self, row):
        # Filters the list box with the text from the search entry.
        if self.search_entry.get_text_length() == 0:
            return True

        if row is not self.row_keystroke:
            description = row.description.casefold()
        else:
            description = self.row_keystroke_label.get_label().casefold()
        search = self.search_entry.get_text().casefold()

        for term in search.split(" "):
            if term not in description:
                return False
        return True

    def _get_button_name_and_description(self, button):
        # Translators: the {} will be replaced with the button index, e.g.
        # "Button 1 click".
        name = _("Button {} click").format(button.index)
        if button.index in RatbagdButton.BUTTON_DESCRIPTION:
            description = _(RatbagdButton.BUTTON_DESCRIPTION[button.index])
        else:
            description = name
        return name, description

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
        # Overrides Gtk.Window's standard key press event callback, so we can
        # capture the pressed buttons in capture mode. If we're not in capture
        # mode, we trigger the search bar on any key press.
        if self.stack.get_visible_child_name() != "capture":
            if self.search_bar.handle_event(event) == Gdk.EVENT_STOP:
                return Gdk.EVENT_STOP
            return Gtk.Window.do_key_press_event(self, event)
        return self._do_key_event(event)

    def do_key_release_event(self, event):
        # Overrides Gtk.Window's standard key release event callback, so we can
        # capture the released buttons in capture mode. If we're not in capture
        # mode, we pass the event on to other widgets in the dialog.
        if self.stack.get_visible_child_name() != "capture":
            return Gtk.Window.do_key_release_event(self, event)
        return self._do_key_event(event)

    def _do_key_event(self, event):
        # Normalize tab.
        if event.keyval == Gdk.KEY_ISO_Left_Tab:
            event.keyval = Gdk.KEY_Tab

        # HACK: we don't want to use SysRq as a keybinding, but we do want
        # Al+Print, so we avoid translating Alt+Print to SysRq.
        if event.keyval == Gdk.KEY_Sys_Req and (event.state & Gdk.ModifierType.MOD1_MASK):
            event.keyval = Gdk.KEY_Print

        if event.type == Gdk.EventType.KEY_PRESS:
            type = RatbagdButton.Macro.KEY_PRESS
        elif event.type == Gdk.EventType.KEY_RELEASE:
            type = RatbagdButton.Macro.KEY_RELEASE

        # TODO: this needs to be checked for its Wayland support.
        if not self._XORG_KEYCODE_OFFSET <= event.hardware_keycode <= 255:
            print("Keycode is not within the valid range.", file=sys.stderr)
        else:
            self._current_macro.append(type, event.hardware_keycode - self._XORG_KEYCODE_OFFSET)
        return Gdk.EVENT_STOP

    def _on_macro_updated(self, macro, pspec):
        current_macro = str(self._current_macro)
        self.label_keystroke.set_label(current_macro)
        self.label_preview.set_label(current_macro)

    def _on_macro_set(self, macro):
        # A macro has been set; update accordingly.
        self._action_type = RatbagdButton.ActionType.MACRO
        self._mapping = macro
        self.stack.set_visible_child_name("overview")
        self._release_grab()

    @GtkTemplate.Callback
    def _on_row_activated(self, listbox, row):
        if row == self.row_keystroke:
            if self._grab_seat() is not True:
                # TODO: display this somewhere in the UI instead.
                print("Unable to grab keyboard, can't set keystroke", file=sys.stderr)
            else:
                self._create_current_macro()
                self.stack.set_visible_child_name("capture")
        else:
            self._action_type = row._action_type
            self._mapping = row._value

    @GtkTemplate.Callback
    def _on_apply_button_clicked(self, button):
        if self.stack.get_visible_child_name() == "capture":
            self._current_macro.accept()
        return Gdk.EVENT_PROPAGATE

    @GtkTemplate.Callback
    def _on_primary_mode_toggled(self, toggle):
        if not toggle.get_active():
            return
        self._action_type = RatbagdButton.ActionType.BUTTON
        if toggle is self.radio_left_handed:
            self._mapping = ButtonDialog.LEFT_HANDED_MODE
        elif toggle is self.radio_right_handed:
            self._mapping = ButtonDialog.RIGHT_HANDED_MODE

    @GObject.Property
    def action_type(self):
        """The action type as last set in the dialog, one of RatbagdButton.ActionType.*."""
        return self._action_type

    @GObject.Property
    def mapping(self):
        """The mapping as last set in the dialog. Note that the type depends on
        action_type, and as such you should check that before using this
        property. A custom value of ButtonDialog.LEFT_HANDED_MODE means that
        the left- and right mouse buttons should be swapped, whereas
        ButtonDialog.RIGHT_HANDED_MODE means that the buttons should be as
        usual."""
        return self._mapping
