"""Linux settings window (GTK3 UI)."""

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk

from claudy.content.ui_text import (
    GIFT_COOLDOWN_OPTIONS, GIFT_DURATION_OPTIONS, GIFT_LIMIT_OPTIONS,
    LANGUAGE_OPTIONS, SCHEDULE_OPTIONS, SPEECH_OPTIONS, label, localized,
)
from claudy.core.settings import (
    DOCK_ICONS_MAX, DOCK_ICONS_MIN, LINUX_TERMINAL_OPTIONS, Settings,
    VERTICAL_OFFSET_MAX, VERTICAL_OFFSET_MIN,
)


class _Choice:
    """A drop-down bound to one setting."""

    def __init__(self, options, current):
        self.keys = [key for key, _ in options]
        self.combo = Gtk.ComboBoxText()
        for _, title in options:
            self.combo.append_text(title)
        self.combo.set_active(
            self.keys.index(current) if current in self.keys else 0)

    def value(self):
        idx = self.combo.get_active()
        return self.keys[idx] if idx >= 0 else None


class SettingsWindow:
    """A GTK3 settings dialog."""

    def __init__(self):
        self.window = None
        self.settings = Settings.shared()
        self._orig_vertical_offset = None
        self._saved = False

    def show(self):
        if self.window and self.window.get_visible():
            self.window.present()
            return

        s = self.settings
        lang = s.language
        # Remember the height so we can revert if the user closes without
        # saving (the scale previews live by mutating the shared settings).
        self._orig_vertical_offset = s.vertical_offset
        self._saved = False
        self.window = Gtk.Window(title=label("title", lang))
        self.window.set_default_size(320, 520)
        self.window.set_resizable(False)
        self.window.set_position(Gtk.WindowPosition.CENTER)
        self.window.connect("delete-event", self._on_close)

        self._grid = Gtk.Grid()
        self._grid.set_column_spacing(12)
        self._grid.set_row_spacing(8)
        for side in ("start", "end", "top", "bottom"):
            getattr(self._grid, f"set_margin_{side}")(20)
        self._row = 0

        self._choices = {}
        terminals = [(t, t) for t in LINUX_TERMINAL_OPTIONS]
        self._add_choice("terminal", "terminal", terminals, s.terminal)
        self._add_choice("schedule", "schedule",
                         localized(SCHEDULE_OPTIONS, lang), s.schedule)

        # Height above the panel (scale previews live as you drag)
        self._add_label(label("height", lang))
        self.height_scale = Gtk.Scale.new_with_range(
            Gtk.Orientation.HORIZONTAL,
            VERTICAL_OFFSET_MIN, VERTICAL_OFFSET_MAX, 1)
        self.height_scale.set_value(s.vertical_offset)
        self.height_scale.set_value_pos(Gtk.PositionType.RIGHT)
        for value, key in ((VERTICAL_OFFSET_MIN, "height_below"),
                           (0, "height_dock"),
                           (VERTICAL_OFFSET_MAX, "height_above")):
            self.height_scale.add_mark(
                value, Gtk.PositionType.BOTTOM, label(key, lang))
        self.height_scale.connect("format-value", self._format_height)
        self.height_scale.connect("value-changed", self._on_height_changed)
        self._add_widget(self.height_scale)

        # Dock icons (estimates the Dock width so Claudy paces only across it)
        self._add_label(label("dock_icons", lang))
        self.dock_icons_scale = Gtk.Scale.new_with_range(
            Gtk.Orientation.HORIZONTAL, DOCK_ICONS_MIN, DOCK_ICONS_MAX, 1)
        self.dock_icons_scale.set_value(s.dock_icons)
        self.dock_icons_scale.set_value_pos(Gtk.PositionType.RIGHT)
        self.dock_icons_scale.connect(
            "format-value", lambda _scale, value: str(int(round(value))))
        self._add_widget(self.dock_icons_scale)
        hint = Gtk.Label(label=label("dock_icons_hint", lang), xalign=0)
        hint.get_style_context().add_class("dim-label")
        self._add_widget(hint)

        self._add_choice("language", "language", LANGUAGE_OPTIONS, s.language)

        self._add_label(label("name", lang))
        self.name_entry = Gtk.Entry()
        self.name_entry.set_text(s.user_name or "")
        self._add_widget(self.name_entry)

        self._add_choice("speech_interval", "speech",
                         localized(SPEECH_OPTIONS, lang), s.speech_interval)
        self._add_choice("gift_duration", "gift_dur",
                         localized(GIFT_DURATION_OPTIONS, lang), s.gift_duration)
        self._add_choice("gift_limit", "gift_lim",
                         localized(GIFT_LIMIT_OPTIONS, lang), s.gift_limit)
        self._add_choice("gift_cooldown", "gift_cd",
                         localized(GIFT_COOLDOWN_OPTIONS, lang), s.gift_cooldown)

        self.dev_check = Gtk.CheckButton(label=label("dev", lang))
        self.dev_check.set_active(s.dev_mode)
        self._add_widget(self.dev_check)

        save_btn = Gtk.Button(label=label("save", lang))
        save_btn.connect("clicked", self._on_save)
        self._add_widget(save_btn)

        self.window.add(self._grid)
        self.window.show_all()

    def _add_widget(self, widget):
        self._grid.attach(widget, 0, self._row, 2, 1)
        self._row += 1

    def _add_label(self, text):
        self._add_widget(Gtk.Label(label=text, xalign=0))

    def _add_choice(self, setting, label_key, options, current):
        self._add_label(label(label_key, self.settings.language))
        choice = _Choice(options, current)
        self._add_widget(choice.combo)
        self._choices[setting] = choice

    def _on_save(self, button):
        for setting, choice in self._choices.items():
            value = choice.value()
            if value is not None:
                setattr(self.settings, setting, value)
        self.settings.user_name = self.name_entry.get_text().strip()
        self.settings.dev_mode = self.dev_check.get_active()
        self.settings.vertical_offset = self.height_scale.get_value()
        self.settings.dock_icons = self.dock_icons_scale.get_value()

        self._saved = True
        self.settings.save()
        self.window.close()

    def _on_height_changed(self, scale):
        # Preview live by mutating the shared settings; the running crab reads
        # vertical_offset every tick, so it rises/lowers as the scale moves.
        self.settings.vertical_offset = scale.get_value()

    def _format_height(self, scale, value):
        lang = self.settings.language
        v = int(round(value))
        if v == 0:
            return label("height_dock", lang)
        return "%+d %s" % (v, label("height_unit", lang))

    def _on_close(self, window, event):
        # Revert the live preview if the user closed without saving.
        if not self._saved and self._orig_vertical_offset is not None:
            self.settings.vertical_offset = self._orig_vertical_offset
        self.window = None
        return False
