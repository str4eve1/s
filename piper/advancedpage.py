# SPDX-License-Identifier: GPL-2.0-or-later

import gi

from .mousemap import MouseMap
from .ratbagd import RatbagdDevice, RatbagdProfile

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk  # noqa: E402


@Gtk.Template(resource_path="/org/freedesktop/Piper/ui/AdvancedPage.ui")
class AdvancedPage(Gtk.Box):
    """
    Advanced settings stack.
    """

    __gtype_name__ = "AdvancedPage"

    angle_snapping: Gtk.Switch = Gtk.Template.Child()  # type: ignore
    debounce: Gtk.ComboBox = Gtk.Template.Child()  # type: ignore
    rate_1000: Gtk.RadioButton = Gtk.Template.Child()  # type: ignore
    rate_125: Gtk.RadioButton = Gtk.Template.Child()  # type: ignore
    rate_250: Gtk.RadioButton = Gtk.Template.Child()  # type: ignore
    rate_500: Gtk.RadioButton = Gtk.Template.Child()  # type: ignore
    rate_button_box: Gtk.ButtonBox = Gtk.Template.Child()  # type: ignore

    def __init__(
        self, device: RatbagdDevice, profile: RatbagdProfile, *args, **kwargs
    ) -> None:
        """Instantiates a new AdvancedPage."""
        Gtk.Box.__init__(self, *args, **kwargs)

        self._profile = profile

        self._handler_debounce = self.debounce.connect(
            "changed", self._on_debounce_changed
        )
        self._handler_snapping = self.angle_snapping.connect(
            "state-set", self._on_snapping_state_set
        )

        self.rate_125.set_active(profile.report_rate == 125)
        self.rate_250.set_active(profile.report_rate == 250)
        self.rate_500.set_active(profile.report_rate == 500)
        self.rate_1000.set_active(profile.report_rate == 1000)

        are_report_rates_supported = (
            profile.report_rate != 0 and len(profile.report_rates) != 0
        )
        self.rate_button_box.set_sensitive(are_report_rates_supported)
        self.rate_125.set_sensitive(125 in profile.report_rates)
        self.rate_250.set_sensitive(250 in profile.report_rates)
        self.rate_500.set_sensitive(500 in profile.report_rates)
        self.rate_1000.set_sensitive(1000 in profile.report_rates)

        self._handler_125 = self.rate_125.connect(
            "toggled", self._on_report_rate_toggled, 125
        )
        self._handler_250 = self.rate_250.connect(
            "toggled", self._on_report_rate_toggled, 250
        )
        self._handler_500 = self.rate_500.connect(
            "toggled", self._on_report_rate_toggled, 500
        )
        self._handler_1000 = self.rate_1000.connect(
            "toggled", self._on_report_rate_toggled, 1000
        )

        profile = self._profile

        self._mousemap = MouseMap("#Buttons", device, spacing=20, border_width=20)
        self.pack_start(self._mousemap, True, True, 0)

        cell = Gtk.CellRendererText()
        self.debounce.pack_start(cell, True)
        self.debounce.add_attribute(cell, "text", 0)

        model = Gtk.ListStore(str)
        for ms in profile.debounces:
            model.append([str(ms)])
        self.debounce.set_model(model)

        self.angle_snapping.set_sensitive(profile.angle_snapping != -1)

        with self.debounce.handler_block(self._handler_debounce):
            if profile.debounce in profile.debounces:
                idx = profile.debounces.index(profile.debounce)
                self.debounce.set_active(idx)
            else:
                self.debounce.set_active(0)

        with self.angle_snapping.handler_block(self._handler_snapping):
            self.angle_snapping.set_active(profile.angle_snapping == 1)

        self.show_all()

    def _on_debounce_changed(self, combo: Gtk.ComboBox) -> None:
        idx = combo.get_active()
        profile = self._profile
        profile.debounce = profile.debounces[idx]

    def _on_snapping_state_set(self, button: Gtk.Switch, state: bool) -> None:
        profile = self._profile
        profile.angle_snapping = 1 if state else 0

    def _on_report_rate_toggled(self, button: Gtk.RadioButton, rate: int) -> None:
        if not button.get_active():
            return
        profile = self._profile
        profile.report_rate = rate
