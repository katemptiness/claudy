"""Claudy — desktop companion for Linux (GTK3)."""

import os
import shutil
import signal
import subprocess
import time

import gi
gi.require_version('Gtk', '3.0')
gi.require_version('Gdk', '3.0')
from gi.repository import Gtk, Gdk, GLib
import cairo

from claudy.backends.linux.bubble import BubbleWindow
from claudy.backends.linux.canvas import CairoCanvas, clear, new_image_cache
from claudy.backends.linux.events import SystemEventHandler
from claudy.backends.linux.gifts_ui import GiftsWindow
from claudy.backends.linux.settings_ui import SettingsWindow
from claudy.backends.linux.windows import (
    make_overlay_window, take_clicks_only_in,
)
from claudy.config import (
    DOCK_DEFAULT_TILE_SIZE, DOCK_TILE_GAP, OVERLAY_HEIGHT, SPRITE_SIZE,
    SPRITE_X, SPRITE_Y, STAR_WINDOW, TICK_INTERVAL, WINDOW_HEIGHT,
    WINDOW_WIDTH,
)
from claudy.content import ui_text
from claudy.core.controller import Controller, Platform
from claudy.core.settings import Settings
from claudy.log import log
from claudy.render.scene import Scene, star_offset_x

CLAUDE_DESKTOP_ID = "com.anthropic.Claude"
CLAUDE_WEB_URL = "https://claude.ai"

# The crab window's bottom edge overlaps the panel by this much
PANEL_OVERLAP = 15
# Wait this long after a click to see whether it becomes a double-click
DOUBLE_CLICK_MS = 350
# After the monitors change, look at the screen once more this much later
SCREEN_SETTLE_S = 2


def _find_claude_desktop_entry():
    """Locate the Claude app's .desktop entry across the XDG data dirs."""
    data_home = os.environ.get("XDG_DATA_HOME") or \
        os.path.expanduser("~/.local/share")
    data_dirs = [data_home] + os.environ.get(
        "XDG_DATA_DIRS", "/usr/local/share:/usr/share").split(":")
    for d in data_dirs:
        if not d:
            continue
        path = os.path.join(d, "applications", CLAUDE_DESKTOP_ID + ".desktop")
        if os.path.isfile(path):
            return path
    return None


def _launch(argv):
    try:
        subprocess.Popen(argv)
    except OSError:
        log.exception("failed to launch %s", argv[0])


def open_claude():
    """Open the Claude desktop app, falling back to the web version.

    On Linux the app ships as com.anthropic.Claude; if it isn't installed we
    still open claude.ai in the browser.
    """
    entry = _find_claude_desktop_entry()
    if entry and shutil.which("gtk-launch"):
        _launch(["gtk-launch", CLAUDE_DESKTOP_ID])
    elif shutil.which("claude-desktop"):
        _launch(["claude-desktop"])
    elif entry and shutil.which("gio"):
        _launch(["gio", "launch", entry])
    else:
        _launch(["xdg-open", CLAUDE_WEB_URL])


def get_screen_geometry():
    """Primary monitor geometry for positioning the crab.

    Returns (monitor_x, monitor_width, base_y), where base_y is the absolute
    screen Y Claudy's feet rest on: the top of a bottom panel if there is
    one, else the bottom of the screen. None if there is no monitor at all,
    as can happen for a moment while monitors change.
    """
    display = Gdk.Display.get_default()
    monitor = display.get_primary_monitor() or display.get_monitor(0)
    if monitor is None:
        return None
    geom = monitor.get_geometry()
    workarea = monitor.get_workarea()

    monitor_bottom = geom.y + geom.height
    work_bottom = workarea.y + workarea.height
    has_bottom_panel = monitor_bottom - work_bottom >= 4
    base_y = work_bottom if has_bottom_panel else monitor_bottom
    return geom.x, geom.width, base_y


class LinuxPlatform(Platform):
    """Linux implementations of what the controller needs."""

    def __init__(self, app):
        self._app = app
        self._settings_window = SettingsWindow()
        self._gifts_window = GiftsWindow()

    def open_claude(self):
        open_claude()

    def open_claude_code(self):
        terminal = Settings.shared().terminal
        if terminal == "kitty":
            _launch(["kitty", "claude"])
        elif terminal == "alacritty":
            _launch(["alacritty", "-e", "claude"])
        else:
            _launch(["gnome-terminal", "--", "claude"])

    def open_settings(self):
        self._settings_window.show()

    def open_gifts(self):
        self._gifts_window.show()

    def show_about(self):
        dialog = Gtk.AboutDialog()
        dialog.set_program_name("Claudy")
        dialog.set_comments(ui_text.about_text("GTK3"))
        dialog.run()
        dialog.destroy()

    def quit(self):
        Gtk.main_quit()


class CrabApp:
    """Main Claudy application for Linux."""

    def __init__(self):
        self._settings = Settings.shared()

        # Screen geometry (absolute screen coords). The controller works in
        # monitor-relative X (0..monitor_w); _abs_x converts.
        self._monitor_x, self._monitor_width, self._base_y = get_screen_geometry()
        screen = Gdk.Screen.get_default()
        screen.connect("monitors-changed", self._on_screen_changed)
        screen.connect("size-changed", self._on_screen_changed)

        self._click_timer = None
        self._spots = {}  # window -> where it was last moved to

        # No Dock-tilesize query on Linux; use the default icon pitch.
        self.controller = Controller(
            LinuxPlatform(self), self._monitor_width,
            dock_tile_pitch=DOCK_DEFAULT_TILE_SIZE + DOCK_TILE_GAP)
        self.system_events = SystemEventHandler(self.controller)

        self.scene = Scene(self.controller)
        self.images = new_image_cache()
        self.bubble = BubbleWindow(self.scene, self.images)

        self._create_windows()
        self.last_tick = time.monotonic()
        GLib.timeout_add(int(TICK_INTERVAL * 1000), self._tick)

    # ---- Windows ----

    def _create_windows(self):
        """Create the crab window and the click-through ground overlay."""
        self.window = make_overlay_window()
        self.window.set_default_size(WINDOW_WIDTH, WINDOW_HEIGHT)
        # Only the sprite takes clicks; the rest of the window passes through
        take_clicks_only_in(self.window, cairo.Region(cairo.RectangleInt(
            SPRITE_X, SPRITE_Y, SPRITE_SIZE, SPRITE_SIZE)))
        self.drawing_area = Gtk.DrawingArea()
        self.drawing_area.set_events(
            Gdk.EventMask.BUTTON_PRESS_MASK
            | Gdk.EventMask.ENTER_NOTIFY_MASK
            | Gdk.EventMask.LEAVE_NOTIFY_MASK)
        self.drawing_area.connect("draw", self._on_draw_main)
        self.drawing_area.connect("button-press-event", self._on_button_press)
        self.drawing_area.connect("enter-notify-event",
                                  lambda *_: self.controller.on_hover(True))
        self.drawing_area.connect("leave-notify-event",
                                  lambda *_: self.controller.on_hover(False))
        self.window.add(self.drawing_area)

        self.ground_window = make_overlay_window(click_through=True)
        self.ground_window.set_default_size(WINDOW_WIDTH, OVERLAY_HEIGHT)
        self.ground_area = Gtk.DrawingArea()
        self.ground_area.connect("draw", self._on_draw_ground)
        self.ground_window.add(self.ground_area)

        # The named star keeps a fixed spot in the sky, so it cannot live in
        # the overlay: that one rides along with Claudy as he paces the panel
        self.star_window = make_overlay_window(click_through=True)
        self.star_window.set_default_size(STAR_WINDOW, STAR_WINDOW)
        self.star_area = Gtk.DrawingArea()
        self.star_area.connect("draw", self._on_draw_star)
        self.star_window.add(self.star_area)

        self._move_windows(self.controller.view)
        # Ground overlay first (behind), then the crab in front
        self.ground_window.show_all()
        self.window.show_all()
        self._place_star()
        self.window.present()

    def _move(self, window, x, y):
        """Move a window, unless it is already there.

        Windows are placed every frame, GTK hands each move straight to the
        X server, and Claudy holds still most of the time.
        """
        if self._spots.get(window) != (x, y):
            self._spots[window] = (x, y)
            window.move(x, y)

    def _place_star(self):
        """Hang the named star in its spot, or hide it in daylight."""
        star = self.controller.star
        if star is None:
            if self.star_window.get_visible():
                self.star_window.hide()
            # Placed afresh at nightfall: GTK may show a hidden window
            # where it was first put, not where it was last moved
            self._spots.pop(self.star_window, None)
            return
        self._move(
            self.star_window,
            int(self._monitor_x + self._monitor_width / 2
                + star_offset_x(star["name"]) - STAR_WINDOW / 2),
            self._win_y() + WINDOW_HEIGHT - self._settings.star_height
            - STAR_WINDOW)
        if not self.star_window.get_visible():
            self.star_window.show_all()

    def _abs_x(self, x):
        """Convert controller X to absolute screen X."""
        return self._monitor_x + x

    def _win_y(self, y_offset=0):
        """Top of the crab window in screen coords (Y grows downward).

        Reads vertical_offset live so the height setting (and its slider
        preview) applies immediately.
        """
        return int(self._base_y - WINDOW_HEIGHT + PANEL_OVERLAP - y_offset
                   - self._settings.vertical_offset)

    def _move_windows(self, view):
        """The crab window follows Claudy up and down; the overlay stays on
        the ground. The bubble's tail points at the crab window's top."""
        win_x = int(self._abs_x(view["x"]) - WINDOW_WIDTH / 2)
        win_y = self._win_y(view["y_offset"])
        self._move(self.window, win_x, win_y)
        self._move(self.ground_window,
                   win_x, self._win_y() + WINDOW_HEIGHT - OVERLAY_HEIGHT)
        self.bubble.sync(self.controller.speech, self._abs_x(view["x"]), win_y)

    def _on_screen_changed(self, screen):
        """A monitor came, went or changed size: find the panel again.

        The desktop rearranges its panels after that, and the workarea
        follows them, so look once more a moment later as well.
        """
        self._follow_screen()
        GLib.timeout_add_seconds(SCREEN_SETTLE_S, self._follow_screen)

    def _follow_screen(self):
        """Re-read the primary monitor; the windows follow on the next tick."""
        geometry = get_screen_geometry()
        if geometry is not None:
            self._monitor_x, self._monitor_width, self._base_y = geometry
            # Claudy paces the new width from the next frame on, when the
            # controller works out his walking bounds again
            self.controller.character.screen_width = self._monitor_width
        return False  # once, also when run as a timeout

    # ---- Drawing ----

    def _on_draw_main(self, widget, cr):
        clear(cr)
        self.scene.paint_crab(CairoCanvas(cr, self.images))

    def _on_draw_ground(self, widget, cr):
        clear(cr)
        self.scene.paint_ground(CairoCanvas(cr, self.images))

    def _on_draw_star(self, widget, cr):
        clear(cr)
        self.scene.paint_star(CairoCanvas(cr, self.images))

    # ---- Input ----

    def _on_button_press(self, widget, event):
        if event.button == 3:
            self._show_context_menu(event)
            return True
        if event.button != 1:
            return False

        if self._click_timer:
            GLib.source_remove(self._click_timer)
            self._click_timer = None
        # GTK delivers _2BUTTON_PRESS for double-clicks automatically
        if event.type == Gdk.EventType._2BUTTON_PRESS:
            self.controller.on_double_click()
        else:
            # Single press — wait to see if a double-click follows
            self._click_timer = GLib.timeout_add(
                DOUBLE_CLICK_MS, self._single_click_fired)
        return True

    def _single_click_fired(self):
        self._click_timer = None
        self.controller.on_click()
        return False

    def _show_context_menu(self, event):
        menu = self._build_menu(self.controller.menu())
        menu.show_all()
        menu.popup_at_pointer(event)

    def _build_menu(self, items):
        menu = Gtk.Menu()
        for item in items:
            if item.separator:
                menu.append(Gtk.SeparatorMenuItem())
                continue
            widget = Gtk.MenuItem(label=item.label)
            widget.set_sensitive(item.enabled)
            if item.submenu:
                widget.set_submenu(self._build_menu(item.submenu))
            elif item.action:
                widget.connect("activate", lambda _w, a=item.action: a())
            menu.append(widget)
        return menu

    # ---- Main loop ----

    def _tick(self):
        now = time.monotonic()
        dt = (now - self.last_tick) * 1000
        self.last_tick = now
        try:
            view = self.controller.tick(dt)
            self._move_windows(view)
            # Only redraw what changed: Claudy is still most of the time, and
            # repainting both windows every frame costs several times the CPU
            if self.scene.crab_changed():
                self.drawing_area.queue_draw()
            if self.scene.ground_changed():
                self.ground_area.queue_draw()
            self._place_star()
            if self.scene.star_changed():
                self.star_area.queue_draw()
        except Exception:
            # An exception here would silently stop the GLib timer (and
            # freeze Claudy), so log it and keep going.
            log.exception("tick failed")
        return True


def main():
    signal.signal(signal.SIGINT, lambda *_: Gtk.main_quit())
    CrabApp()
    Gtk.main()
