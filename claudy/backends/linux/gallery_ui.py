"""Linux gallery window: the paintings Claudy has given (GTK3 UI).

What to show comes from core.gallery; this only lays it out: a grid of the
paintings, the newest first, each under its title, and below it the story
of whichever one is picked.
"""

import cairo
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import GLib, Gtk, Pango

from claudy.backends.linux.canvas import make_image
from claudy.content.ui_text import gallery_header, label
from claudy.core import gallery
from claudy.core.memory import Memory
from claudy.core.settings import Settings
from claudy.render import art
from claudy.render.art import PixelImage

COLUMNS = 4
FRAME = 70          # a painting's side in the window: twice its size on the Dock
STORY_H = 150


def _painting_surface(item):
    """The painting as a Cairo surface FRAME pixels wide."""
    pixels = art.build(art.item_key(item))
    return make_image(PixelImage(pixels.rows, FRAME // len(pixels.rows[0])))


def _draw_painting(area, cr, surface):
    cr.set_source_surface(surface, 0, 0)
    # Crisp pixels on a HiDPI screen, where GTK scales the context up
    cr.get_source().set_filter(cairo.FILTER_NEAREST)
    cr.paint()
    return False


class GalleryWindow:
    """A GTK3 window showing the paintings in the user's gallery."""

    def __init__(self):
        self.window = None
        self._paintings = []
        self.buttons = []
        self.story = None
        self._grid = None           # kept, so the buttons keep their handlers
        self._story_scroll = None

    def show(self):
        """Open the gallery, or bring it forward, freshly hung."""
        if self.window is None:
            self.window = Gtk.Window(title=label("gallery_title"))
            self.window.set_default_size(480, -1)
            self.window.set_resizable(False)
            self.window.set_position(Gtk.WindowPosition.CENTER)
            self.window.connect("delete-event", self._on_close)
        self._hang_paintings()
        self.window.present()

    def refresh(self):
        """Rehang the gallery if it is open: a painting was just taken."""
        if self.window and self.window.get_visible():
            self._hang_paintings()

    def _hang_paintings(self):
        """Lay the gallery out afresh from memory."""
        entries = Memory.shared().get_gallery()
        self._paintings = gallery.paintings(
            entries, name=Settings.shared().user_name or "")
        old = self.window.get_child()
        if old is not None:
            self.window.remove(old)

        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        header = Gtk.Label()
        header.set_markup("<big><b>{}</b></big>".format(GLib.markup_escape_text(
            gallery_header(gallery.copies_given(entries)))))
        header.set_xalign(0)
        header.set_margin_start(16)
        header.set_margin_top(16)
        header.set_margin_bottom(8)
        vbox.pack_start(header, False, False, 0)
        vbox.pack_start(Gtk.Separator(), False, False, 0)

        self.buttons = []
        if not self._paintings:
            empty = Gtk.Label(label=label("no_paintings"))
            empty.set_line_wrap(True)
            empty.set_max_width_chars(40)
            empty.set_margin_top(24)
            empty.set_margin_bottom(32)
            empty.set_opacity(0.6)
            vbox.pack_start(empty, False, False, 0)
        else:
            vbox.pack_start(self._build_grid(), False, False, 0)
            vbox.pack_start(Gtk.Separator(), False, False, 0)
            vbox.pack_start(self._build_story(), False, False, 0)
            self._select(0)

        self.window.add(vbox)
        self.window.show_all()

    def _build_grid(self):
        grid = Gtk.Grid()
        grid.set_column_homogeneous(True)
        grid.set_row_spacing(10)
        grid.set_column_spacing(6)
        grid.set_margin_start(16)
        grid.set_margin_end(16)
        grid.set_margin_top(14)
        grid.set_margin_bottom(14)
        for i, painting in enumerate(self._paintings):
            cell = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)

            area = Gtk.DrawingArea()
            area.set_size_request(FRAME, FRAME)
            area.connect("draw", _draw_painting,
                         _painting_surface(painting.item))
            button = Gtk.Button()
            button.add(area)
            button.set_relief(Gtk.ReliefStyle.NONE)
            button.set_halign(Gtk.Align.CENTER)
            button.set_tooltip_text(painting.title)
            button.connect("clicked", lambda _b, index=i: self._select(index))
            self.buttons.append(button)
            cell.pack_start(button, False, False, 0)

            title = painting.title
            if painting.count > 1:
                title += f"  ×{painting.count}"
            caption = Gtk.Label(label=title)
            caption.set_line_wrap(True)
            caption.set_justify(Gtk.Justification.CENTER)
            caption.set_max_width_chars(14)
            cell.pack_start(caption, False, False, 0)

            grid.attach(cell, i % COLUMNS, i // COLUMNS, 1, 1)
        self._grid = grid
        return grid

    def _build_story(self):
        scroll = Gtk.ScrolledWindow()
        scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        scroll.set_size_request(-1, STORY_H)
        self.story = Gtk.Label()
        self.story.set_xalign(0)
        self.story.set_yalign(0)
        self.story.set_line_wrap(True)
        self.story.set_line_wrap_mode(Pango.WrapMode.WORD_CHAR)
        self.story.set_max_width_chars(48)
        self.story.set_margin_start(16)
        self.story.set_margin_end(16)
        self.story.set_margin_top(10)
        self.story.set_margin_bottom(10)
        scroll.add(self.story)
        self._story_scroll = scroll
        return scroll

    def _select(self, index):
        """Pick a painting: frame its button and tell its story."""
        for i, button in enumerate(self.buttons):
            button.set_relief(Gtk.ReliefStyle.NORMAL if i == index
                              else Gtk.ReliefStyle.NONE)
        painting = self._paintings[index]
        parts = [f"<b>{GLib.markup_escape_text(painting.title)}</b>"]
        for copy in painting.copies:
            parts.append(
                f"<small><span alpha='60%'>"
                f"{GLib.markup_escape_text(copy.date)}</span></small>\n"
                f"{GLib.markup_escape_text(copy.story)}")
        self.story.set_markup("\n\n".join(parts))
        # Each story is read from its start
        self._story_scroll.get_vadjustment().set_value(0)

    def _on_close(self, window, event):
        self.window = None
        return False
