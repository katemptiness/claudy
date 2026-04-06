"""Linux settings window (GTK3 UI)."""

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk

from settings import (
    Settings, LANGUAGE_OPTIONS,
    _SCHEDULE_OPTIONS, _SPEECH_OPTIONS,
    _GIFT_DURATION_OPTIONS, _GIFT_LIMIT_OPTIONS,
    _loc, _l,
)

# Linux-specific terminal options
LINUX_TERMINAL_OPTIONS = ["gnome-terminal", "kitty", "alacritty"]


class SettingsWindow:
    """A GTK3 settings dialog."""

    _instance = None

    def __init__(self):
        self.window = None
        self.settings = Settings.shared()

    def show(self):
        if self.window and self.window.get_visible():
            self.window.present()
            return

        lang = self.settings.language
        self.window = Gtk.Window(title=_l("title", lang))
        self.window.set_default_size(320, 520)
        self.window.set_resizable(False)
        self.window.set_position(Gtk.WindowPosition.CENTER)
        self.window.connect("delete-event", self._on_close)

        grid = Gtk.Grid()
        grid.set_column_spacing(12)
        grid.set_row_spacing(8)
        grid.set_margin_start(20)
        grid.set_margin_end(20)
        grid.set_margin_top(20)
        grid.set_margin_bottom(20)
        row = 0

        # Terminal
        grid.attach(Gtk.Label(label=_l("terminal", lang), xalign=0), 0, row, 1, 1)
        row += 1
        self.terminal_combo = Gtk.ComboBoxText()
        for opt in LINUX_TERMINAL_OPTIONS:
            self.terminal_combo.append_text(opt)
        term = self.settings.terminal
        if term in LINUX_TERMINAL_OPTIONS:
            self.terminal_combo.set_active(LINUX_TERMINAL_OPTIONS.index(term))
        else:
            self.terminal_combo.set_active(0)
        grid.attach(self.terminal_combo, 0, row, 2, 1)
        row += 1

        # Schedule
        grid.attach(Gtk.Label(label=_l("schedule", lang), xalign=0), 0, row, 1, 1)
        row += 1
        sched = _loc(_SCHEDULE_OPTIONS, lang)
        self.schedule_combo = Gtk.ComboBoxText()
        sched_keys = []
        for key, title in sched:
            self.schedule_combo.append_text(title)
            sched_keys.append(key)
        self._sched_keys = sched_keys
        idx = sched_keys.index(self.settings.schedule) \
            if self.settings.schedule in sched_keys else 0
        self.schedule_combo.set_active(idx)
        grid.attach(self.schedule_combo, 0, row, 2, 1)
        row += 1

        # Language
        grid.attach(Gtk.Label(label=_l("language", lang), xalign=0), 0, row, 1, 1)
        row += 1
        self.lang_combo = Gtk.ComboBoxText()
        self._lang_keys = []
        for key, title in LANGUAGE_OPTIONS:
            self.lang_combo.append_text(title)
            self._lang_keys.append(key)
        idx = self._lang_keys.index(self.settings.language) \
            if self.settings.language in self._lang_keys else 0
        self.lang_combo.set_active(idx)
        grid.attach(self.lang_combo, 0, row, 2, 1)
        row += 1

        # Name
        grid.attach(Gtk.Label(label=_l("name", lang), xalign=0), 0, row, 1, 1)
        row += 1
        self.name_entry = Gtk.Entry()
        self.name_entry.set_text(self.settings.user_name or "")
        grid.attach(self.name_entry, 0, row, 2, 1)
        row += 1

        # Speech frequency
        grid.attach(Gtk.Label(label=_l("speech", lang), xalign=0), 0, row, 1, 1)
        row += 1
        speech = _loc(_SPEECH_OPTIONS, lang)
        self.speech_combo = Gtk.ComboBoxText()
        self._speech_keys = []
        for key, title in speech:
            self.speech_combo.append_text(title)
            self._speech_keys.append(key)
        idx = self._speech_keys.index(self.settings.speech_interval) \
            if self.settings.speech_interval in self._speech_keys else 1
        self.speech_combo.set_active(idx)
        grid.attach(self.speech_combo, 0, row, 2, 1)
        row += 1

        # Gift duration
        grid.attach(Gtk.Label(label=_l("gift_dur", lang), xalign=0), 0, row, 1, 1)
        row += 1
        gdur = _loc(_GIFT_DURATION_OPTIONS, lang)
        self.gift_dur_combo = Gtk.ComboBoxText()
        self._gdur_keys = []
        for key, title in gdur:
            self.gift_dur_combo.append_text(title)
            self._gdur_keys.append(key)
        idx = self._gdur_keys.index(self.settings.gift_duration) \
            if self.settings.gift_duration in self._gdur_keys else 2
        self.gift_dur_combo.set_active(idx)
        grid.attach(self.gift_dur_combo, 0, row, 2, 1)
        row += 1

        # Gifts per day
        grid.attach(Gtk.Label(label=_l("gift_lim", lang), xalign=0), 0, row, 1, 1)
        row += 1
        glim = _loc(_GIFT_LIMIT_OPTIONS, lang)
        self.gift_lim_combo = Gtk.ComboBoxText()
        self._glim_keys = []
        for key, title in glim:
            self.gift_lim_combo.append_text(title)
            self._glim_keys.append(key)
        idx = self._glim_keys.index(self.settings.gift_limit) \
            if self.settings.gift_limit in self._glim_keys else 1
        self.gift_lim_combo.set_active(idx)
        grid.attach(self.gift_lim_combo, 0, row, 2, 1)
        row += 1

        # Dev mode
        self.dev_check = Gtk.CheckButton(label=_l("dev", lang))
        self.dev_check.set_active(self.settings.dev_mode)
        grid.attach(self.dev_check, 0, row, 2, 1)
        row += 1

        # Save button
        save_btn = Gtk.Button(label=_l("save", lang))
        save_btn.connect("clicked", self._on_save)
        grid.attach(save_btn, 0, row, 2, 1)

        self.window.add(grid)
        self.window.show_all()

    def _on_save(self, button):
        idx = self.terminal_combo.get_active()
        if idx >= 0:
            self.settings.terminal = LINUX_TERMINAL_OPTIONS[idx]

        idx = self.schedule_combo.get_active()
        if idx >= 0:
            self.settings.schedule = self._sched_keys[idx]

        idx = self.lang_combo.get_active()
        if idx >= 0:
            self.settings.language = self._lang_keys[idx]

        self.settings.user_name = self.name_entry.get_text().strip()

        idx = self.speech_combo.get_active()
        if idx >= 0:
            self.settings.speech_interval = self._speech_keys[idx]

        idx = self.gift_dur_combo.get_active()
        if idx >= 0:
            self.settings.gift_duration = self._gdur_keys[idx]

        idx = self.gift_lim_combo.get_active()
        if idx >= 0:
            self.settings.gift_limit = self._glim_keys[idx]

        self.settings.dev_mode = self.dev_check.get_active()

        self.settings.save()
        self.window.close()

    def _on_close(self, window, event):
        self.window = None
        return False
