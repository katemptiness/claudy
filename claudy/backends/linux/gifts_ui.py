"""Linux gifts collection window (GTK3 UI)."""

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Pango

from claudy.content.gift_stories import get_story
from claudy.content.ui_text import (
    format_date, gift_type_name, gifts_header, label,
)
from claudy.core.memory import Memory
from claudy.core.settings import Settings


class GiftsWindow:
    """A GTK3 window showing the user's gift collection."""

    def __init__(self):
        self.window = None

    def show(self):
        if self.window and self.window.get_visible():
            self.window.present()
            return

        gifts = Memory.shared().get_collected_gifts()
        user_name = Settings.shared().user_name or ""

        self.window = Gtk.Window(title=label("gifts_title"))
        self.window.set_default_size(360, 420)
        self.window.set_resizable(True)
        self.window.set_position(Gtk.WindowPosition.CENTER)
        self.window.connect("delete-event", self._on_close)

        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)

        # Header with gift count
        header = Gtk.Label()
        header.set_markup(f"<big><b>{gifts_header(len(gifts))}</b></big>")
        header.set_xalign(0)
        header.set_margin_start(16)
        header.set_margin_top(16)
        header.set_margin_bottom(8)
        vbox.pack_start(header, False, False, 0)

        # Separator
        vbox.pack_start(Gtk.Separator(), False, False, 0)

        if not gifts:
            empty_label = Gtk.Label(label=label("no_gifts"))
            empty_label.set_margin_top(40)
            empty_label.set_opacity(0.6)
            vbox.pack_start(empty_label, True, False, 0)
        else:
            # Scrollable list of gifts
            scroll = Gtk.ScrolledWindow()
            scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)

            listbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
            listbox.set_margin_start(12)
            listbox.set_margin_end(12)
            listbox.set_margin_top(8)
            listbox.set_margin_bottom(12)

            for gift in gifts:
                row = self._build_gift_row(gift, user_name)
                listbox.pack_start(row, False, False, 0)
                listbox.pack_start(Gtk.Separator(), False, False, 0)

            scroll.add(listbox)
            vbox.pack_start(scroll, True, True, 0)

        self.window.add(vbox)
        self.window.show_all()

    def _build_gift_row(self, gift, user_name):
        """Build a single gift row widget."""
        row = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        row.set_margin_top(8)
        row.set_margin_bottom(8)

        # Top line: emoji + type label + date
        top = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)

        emoji_label = Gtk.Label()
        emoji_label.set_markup(f"<span size='x-large'>{gift['emoji']}</span>")
        top.pack_start(emoji_label, False, False, 0)

        type_label = Gtk.Label()
        type_label.set_markup(f"<b>{gift_type_name(gift['type'])}</b>")
        type_label.set_xalign(0)
        top.pack_start(type_label, True, True, 0)

        date_label = Gtk.Label(label=format_date(gift["date"]))
        date_label.set_opacity(0.5)
        top.pack_end(date_label, False, False, 0)

        row.pack_start(top, False, False, 0)

        # Story text
        story_text = get_story(gift["type"], gift["story_id"], name=user_name)
        story_label = Gtk.Label(label=story_text)
        story_label.set_xalign(0)
        story_label.set_line_wrap(True)
        story_label.set_line_wrap_mode(Pango.WrapMode.WORD_CHAR)
        story_label.set_max_width_chars(40)
        story_label.set_opacity(0.75)
        story_label.set_margin_start(4)
        row.pack_start(story_label, False, False, 0)

        return row

    def _on_close(self, window, event):
        self.window = None
        return False

