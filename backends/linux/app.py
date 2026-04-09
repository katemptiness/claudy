"""Claudy — desktop companion for Linux (GTK3)."""

import os
import random
import signal
import subprocess
import time

import gi
gi.require_version('Gtk', '3.0')
gi.require_version('Gdk', '3.0')
gi.require_version('PangoCairo', '1.0')
from gi.repository import Gtk, Gdk, GLib, Pango, PangoCairo
import cairo

from config import (
    SPRITE_SIZE, WINDOW_WIDTH, WINDOW_HEIGHT,
    SPRITE_OFFSET_X, SPRITE_OFFSET_Y, TICK_INTERVAL,
    PARTICLE_WINDOW_HEIGHT,
)

from backends.linux.renderer import SpriteCache
from sprites.base import ALL as BASE_SPRITES
from sprites.activities import ALL as ACTIVITY_SPRITES
from character import Character, ACTIVITIES
from particles import ParticleSystem
from backends.linux.events import SystemEventHandler
from backends.linux.speech import SpeechBubble
from settings import Settings, GIFT_DURATIONS
from backends.linux.settings_ui import SettingsWindow
from backends.linux.gifts_ui import GiftsWindow
from phrases import (t, get_language, format_phrase, GIFT_COLLECT_PHRASES,
                     GIFT_ANNOUNCE_PHRASES, GIFT_EXPIRED_PHRASES)
from memory import Memory


def get_dock_geometry():
    """Get primary monitor geometry for positioning the crab.

    Returns a dict with absolute screen coordinates:
      monitor_x, monitor_y: top-left of the primary monitor
      monitor_w, monitor_h: size of the primary monitor
      crab_base_y: Y where the crab window bottom should sit
    """
    display = Gdk.Display.get_default()
    monitor = display.get_primary_monitor() or display.get_monitor(0)
    geom = monitor.get_geometry()
    workarea = monitor.get_workarea()

    monitor_bottom = geom.y + geom.height
    work_bottom = workarea.y + workarea.height
    bottom_panel = monitor_bottom - work_bottom

    # crab_base_y: the Y where the crab's feet should touch.
    # If there's a bottom panel, sit on top of it. Otherwise, screen bottom.
    if bottom_panel >= 4:
        crab_base_y = work_bottom
    else:
        crab_base_y = monitor_bottom

    return {
        "monitor_x": geom.x,
        "monitor_y": geom.y,
        "monitor_w": geom.width,
        "monitor_h": geom.height,
        "crab_base_y": crab_base_y,
    }


def _make_transparent_window(window_type=Gtk.WindowType.TOPLEVEL):
    """Create a borderless transparent window."""
    win = Gtk.Window(type=window_type)
    win.set_decorated(False)
    win.set_keep_above(True)
    win.set_skip_taskbar_hint(True)
    win.set_skip_pager_hint(True)

    screen = win.get_screen()
    visual = screen.get_rgba_visual()
    if visual:
        win.set_visual(visual)
    win.set_app_paintable(True)

    return win


class CrabApp:
    """Main Claudy application for Linux."""

    def __init__(self):
        self._settings = Settings.shared()
        self._settings_window = SettingsWindow()
        self._gifts_window = GiftsWindow()

        # Build sprite cache
        all_sprites = {}
        all_sprites.update(BASE_SPRITES)
        all_sprites.update(ACTIVITY_SPRITES)
        self.sprite_cache = SpriteCache(all_sprites)

        friend_names = ["idle", "blink", "happy", "love", "wave",
                        "walk_a", "walk_b", "play_a", "play_b"]
        for name in friend_names:
            if name in all_sprites:
                self.sprite_cache.add_friend(name, all_sprites[name])

        # Screen and dock geometry (all absolute screen coords)
        geo = get_dock_geometry()
        self._monitor_x = geo["monitor_x"]
        self._monitor_w = geo["monitor_w"]
        self._crab_base_y = geo["crab_base_y"]

        # Character uses monitor-relative X (0..monitor_w).
        # We add _monitor_x when converting to screen coords.
        self.character = Character(self._monitor_w)
        self.character.x = self._monitor_w / 2

        # Particle system
        self.particles = ParticleSystem()

        # State
        self.gift_layer_emoji = None
        self.gift_timer = None
        self.friend_visible = False
        self.friend_sprite = "idle"

        # Track sprite state for change detection
        self.current_sprite_name = "sleep_a"
        self.current_facing = True

        # Startup animation
        self.startup_phase = 0
        self.startup_timer = 0

        # Click tracking
        self._click_timer = None

        Memory.shared()

        # System events
        self.system_events = SystemEventHandler(self.character)
        self.system_events.set_speech(self._show_event_speech)

        # Speech bubble
        self.speech = SpeechBubble()
        self.speech.setup()

        self._create_windows()

        # Start tick loop
        self.last_tick = time.time()
        GLib.timeout_add(int(TICK_INTERVAL * 1000), self._tick)

    def _create_windows(self):
        """Create the crab window and particle overlay."""
        # --- Main crab window ---
        # POPUP bypasses WM positioning rules so we can sit on the dock
        self.window = _make_transparent_window(Gtk.WindowType.POPUP)
        self.window.set_default_size(WINDOW_WIDTH, WINDOW_HEIGHT)

        self.drawing_area = Gtk.DrawingArea()
        self.drawing_area.set_events(
            Gdk.EventMask.BUTTON_PRESS_MASK
            | Gdk.EventMask.ENTER_NOTIFY_MASK
            | Gdk.EventMask.LEAVE_NOTIFY_MASK
        )
        self.drawing_area.connect("draw", self._on_draw_main)
        self.drawing_area.connect("button-press-event", self._on_button_press)
        self.drawing_area.connect("enter-notify-event", self._on_enter)
        self.drawing_area.connect("leave-notify-event", self._on_leave)

        self.window.add(self.drawing_area)

        # Position at bottom of monitor
        win_x = int(self._abs_x(self.character.x) - WINDOW_WIDTH / 2)
        win_y = self._win_y()
        self.window.move(win_x, win_y)

        # --- Particle overlay window ---
        self.particle_window = _make_transparent_window(Gtk.WindowType.POPUP)
        self.particle_window.set_default_size(WINDOW_WIDTH, PARTICLE_WINDOW_HEIGHT)

        self.particle_area = Gtk.DrawingArea()
        self.particle_area.connect("draw", self._on_draw_particles)
        self.particle_window.add(self.particle_area)

        # Particle window: same bottom edge as main, but taller
        part_y = int(self._crab_base_y - PARTICLE_WINDOW_HEIGHT)
        self.particle_window.move(win_x, part_y)

        # Make particle window click-through: connect BEFORE show
        def make_input_passthrough(widget, *args):
            gdk_win = widget.get_window()
            if gdk_win:
                empty = cairo.Region()
                gdk_win.input_shape_combine_region(empty, 0, 0)
        self.particle_window.connect("realize", make_input_passthrough)

        # Show particle window first (behind), then main window (in front)
        self.particle_window.show_all()
        self.window.show_all()

        # Re-apply input passthrough after show (some WMs need this)
        GLib.idle_add(make_input_passthrough, self.particle_window)

        # Shape main window input to sprite area only (transparent areas pass through)
        def shape_main_input(widget, *args):
            gdk_win = widget.get_window()
            if gdk_win:
                sprite_y = WINDOW_HEIGHT - SPRITE_SIZE
                rect = cairo.RectangleInt(
                    SPRITE_OFFSET_X, sprite_y, SPRITE_SIZE, SPRITE_SIZE)
                region = cairo.Region(rect)
                gdk_win.input_shape_combine_region(region, 0, 0)
        GLib.idle_add(shape_main_input, self.window)

        # Ensure main window stays above particle window
        self.window.present()

    # ---- Coordinate helpers ----
    # character.x is monitor-relative (0..monitor_w).
    # Window positions are absolute screen coords.

    def _abs_x(self, char_x):
        """Convert character X to absolute screen X."""
        return self._monitor_x + char_x

    def _win_y(self, y_offset=0):
        """Get the crab window's Y in screen coords, accounting for bounce."""
        # Place window so its bottom edge overlaps the dock by ~15px
        return int(self._crab_base_y - WINDOW_HEIGHT + 15 - y_offset)

    def _show_event_speech(self, phrase):
        """Show speech from system events (app launches, sleep/wake)."""
        self.speech.show(phrase, self._abs_x(self.character.x), self._win_y())

    # ---- Drawing ----

    def _on_draw_main(self, widget, cr):
        """Draw the crab sprite, shadow, friend, and gift."""
        # Clear to transparent
        cr.set_operator(cairo.OPERATOR_SOURCE)
        cr.set_source_rgba(0, 0, 0, 0)
        cr.paint()
        cr.set_operator(cairo.OPERATOR_OVER)

        # Shadow ellipse
        shadow_w, shadow_h = 50, 8
        shadow_x = SPRITE_OFFSET_X + (SPRITE_SIZE - shadow_w) / 2
        shadow_y = WINDOW_HEIGHT - shadow_h - 1  # near bottom
        cr.save()
        cr.set_source_rgba(0, 0, 0, 0.15)
        cr.translate(shadow_x + shadow_w / 2, shadow_y + shadow_h / 2)
        cr.scale(shadow_w / 2, shadow_h / 2)
        cr.arc(0, 0, 1, 0, 6.2832)
        cr.fill()
        cr.restore()

        # Friend sprite (drawn behind crab, 50px to the left)
        if self.friend_visible:
            friend_name = f"friend_{self.friend_sprite}"
            if self.sprite_cache.has(friend_name):
                surface = self.sprite_cache.get(friend_name)
                friend_x = SPRITE_OFFSET_X - 50
                sprite_y = WINDOW_HEIGHT - SPRITE_SIZE  # bottom of window
                cr.set_source_surface(surface, friend_x, sprite_y)
                cr.get_source().set_filter(cairo.FILTER_NEAREST)
                cr.paint()

        # Crab sprite
        sprite_name = self.current_sprite_name
        if not self.sprite_cache.has(sprite_name):
            sprite_name = "idle"
        surface = self.sprite_cache.get(sprite_name)

        sprite_x = SPRITE_OFFSET_X
        sprite_y = WINDOW_HEIGHT - SPRITE_SIZE  # bottom of window

        # Shake offset
        if self.character.is_shaking:
            sprite_x += (random.random() - 0.5) * 6

        cr.save()
        if not self.current_facing:
            # Horizontal flip: translate to right edge, scale -1
            cr.translate(sprite_x + SPRITE_SIZE, sprite_y)
            cr.scale(-1, 1)
            cr.set_source_surface(surface, 0, 0)
        else:
            cr.set_source_surface(surface, sprite_x, sprite_y)
        cr.get_source().set_filter(cairo.FILTER_NEAREST)
        cr.paint()
        cr.restore()

        # Gift emoji
        if self.gift_layer_emoji:
            cr.set_source_rgba(0, 0, 0, 1)
            layout = widget.create_pango_layout(self.gift_layer_emoji)
            font_desc = Pango.FontDescription("Sans 18")
            layout.set_font_description(font_desc)
            gift_x = SPRITE_OFFSET_X + SPRITE_SIZE + 5
            gift_y = WINDOW_HEIGHT - 30  # near bottom
            cr.move_to(gift_x, gift_y)
            PangoCairo.show_layout(cr, layout)

    def _on_draw_particles(self, widget, cr):
        """Draw floating particles."""
        cr.set_operator(cairo.OPERATOR_SOURCE)
        cr.set_source_rgba(0, 0, 0, 0)
        cr.paint()
        cr.set_operator(cairo.OPERATOR_OVER)

        active = self.particles.get_active()
        for p in active:
            # Flip Y: particle system uses Y-up from bottom of window
            screen_y = PARTICLE_WINDOW_HEIGHT - p.y - 15

            cr.save()
            cr.set_source_rgba(p.color[0], p.color[1], p.color[2], p.opacity)

            layout = widget.create_pango_layout(p.text)
            font_desc = Pango.FontDescription(f"Sans {p.size}")
            layout.set_font_description(font_desc)
            cr.move_to(p.x - 10, screen_y)
            PangoCairo.show_layout(cr, layout)
            cr.restore()

    # ---- Input handling ----

    def _hit_test(self, x, y):
        """Check if (x, y) is within the sprite area."""
        sprite_y = WINDOW_HEIGHT - SPRITE_SIZE
        return (SPRITE_OFFSET_X <= x <= SPRITE_OFFSET_X + SPRITE_SIZE and
                sprite_y <= y <= sprite_y + SPRITE_SIZE)

    def _on_button_press(self, widget, event):
        if event.button == 3:
            self._show_context_menu(event)
            return True

        if event.button != 1:
            return False
        if not self._hit_test(event.x, event.y):
            return False

        # GTK delivers _2BUTTON_PRESS for double-clicks automatically
        if event.type == Gdk.EventType._2BUTTON_PRESS:
            # Double-click: open Claude in browser
            if self._click_timer:
                GLib.source_remove(self._click_timer)
                self._click_timer = None
            try:
                subprocess.Popen(['xdg-open', 'https://claude.ai'])
            except Exception:
                pass
            return True

        # Single press — wait to see if a double-click follows
        if self._click_timer:
            GLib.source_remove(self._click_timer)
        self._click_timer = GLib.timeout_add(350, self._single_click_fired)

        return True

    def _single_click_fired(self):
        self._click_timer = None
        try:
            Memory.shared().record_click()
        except Exception:
            pass
        if self.gift_layer_emoji:
            self._collect_gift()
            self.character.interrupt("happy")
        elif Memory.shared().is_attached():
            self.character.interrupt("happy_love")
        else:
            self.character.interrupt("happy")
        return False

    def _on_enter(self, widget, event):
        if self.character.state not in ("dragging",) and \
           not self.character.state.startswith("reaction_"):
            self.character.interrupt("wave")

    def _on_leave(self, widget, event):
        if self.character.state == "reaction_wave":
            self.character._enter_idle()

    # ---- Context menu ----

    def _show_context_menu(self, event):
        ru = get_language() == "ru"
        menu = Gtk.Menu()

        def _item(label_en, label_ru, callback):
            label = label_ru if ru else label_en
            item = Gtk.MenuItem(label=label)
            item.connect("activate", callback)
            return item

        menu.append(_item("Open Claude", "Открыть Claude", self._open_claude))
        menu.append(_item("Open Claude Code", "Открыть Claude Code", self._open_claude_code))
        menu.append(Gtk.SeparatorMenuItem())

        # Activities submenu (dev mode only)
        if Settings.shared().dev_mode:
            act_title = "Активности" if ru else "Activities"
            act_item = Gtk.MenuItem(label=act_title)
            act_menu = Gtk.Menu()
            for name in sorted(ACTIVITIES.keys()):
                sub = Gtk.MenuItem(label=name.capitalize())
                sub.connect("activate", self._play_activity, name)
                act_menu.append(sub)
            act_menu.append(Gtk.SeparatorMenuItem())
            tg_title = "Тест подарка" if ru else "Test Gift"
            gift_item = Gtk.MenuItem(label=tg_title)
            gift_item.connect("activate", self._test_gift)
            act_menu.append(gift_item)
            act_item.set_submenu(act_menu)
            menu.append(act_item)
            menu.append(Gtk.SeparatorMenuItem())

        menu.append(_item("Gifts", "Подарки", self._open_gifts))
        menu.append(_item("Settings", "Настройки", self._open_settings))
        menu.append(_item("About Claudy", "О Claudy", self._show_about))
        menu.append(Gtk.SeparatorMenuItem())
        menu.append(_item("Quit", "Выход", self._quit))

        menu.show_all()
        menu.popup_at_pointer(event)

    def _open_claude(self, item):
        try:
            subprocess.Popen(['xdg-open', 'https://claude.ai'])
        except Exception:
            pass

    def _open_claude_code(self, item):
        terminal = self._settings.terminal
        try:
            if terminal == "kitty":
                subprocess.Popen(['kitty', 'claude'])
            elif terminal == "alacritty":
                subprocess.Popen(['alacritty', '-e', 'claude'])
            else:
                # gnome-terminal (default)
                subprocess.Popen(['gnome-terminal', '--', 'claude'])
        except Exception:
            pass

    def _play_activity(self, item, name):
        self.character.friend_visible = False
        self.friend_visible = False
        self.character._enter_idle()
        self.character._start_activity(name)
        # Process events immediately — they'd be cleared on next update()
        for etype, edata in self.character.events:
            if etype == "message":
                self.speech.show(
                    edata, self._abs_x(self.character.x), self._win_y())
        self.character.events = []

    def _test_gift(self, item):
        emojis = ["🐟", "🐡", "💎", "⭐", "🌸", "🦋"]
        self._show_gift(
            {"type": "test", "emoji": random.choice(emojis)},
            self.character.x)

    def _open_gifts(self, item):
        self._gifts_window.show()

    def _open_settings(self, item):
        self._settings_window.show()

    def _show_about(self, item):
        dialog = Gtk.AboutDialog()
        dialog.set_program_name("Claudy")
        if get_language() == "ru":
            dialog.set_comments(
                "Маленький пиксельный краб-компаньон.\n\n"
                "Сделано katemptiness & Claude Opus\n"
                "с любовью и GTK3."
            )
        else:
            dialog.set_comments(
                "A little pixel crab companion for your desktop.\n\n"
                "Made by katemptiness & Claude Opus\n"
                "with love and GTK3."
            )
        dialog.run()
        dialog.destroy()

    def _quit(self, item):
        Gtk.main_quit()

    # ---- Gift system ----

    def _show_gift(self, data, crab_x):
        try:
            if self.gift_layer_emoji:
                return
            if Memory.shared().get_pending_gift():
                return

            limit = Settings.shared().gift_limit
            if limit > 0:
                today_gifts = sum(
                    1 for g in Memory.shared()._data["gifts"]
                    if g.get("date") == Memory.shared()._data["today"]["date"]
                    and g.get("type") != "star")
                if today_gifts >= limit:
                    return

            Memory.shared().add_gift(data["type"], data["emoji"])
            self.gift_layer_emoji = str(data["emoji"])

            self.character.gift_waiting = True
            self.character._enter_idle()

            name = Settings.shared().user_name
            duration = GIFT_DURATIONS.get(Settings.shared().gift_duration, 300)
            phrase = format_phrase(
                random.choice(GIFT_ANNOUNCE_PHRASES), name=name)

            crab_screen_y = self._win_y()
            self.speech.show_persistent(
                phrase, self._abs_x(crab_x), crab_screen_y, duration=float(duration))

            if self.gift_timer:
                GLib.source_remove(self.gift_timer)
            self.gift_timer = GLib.timeout_add(
                int(duration * 1000), self._gift_expired)
        except Exception:
            pass

    def _gift_expired(self):
        self._hide_gift()
        Memory.shared().collect_gift()
        self.speech.clear_persistent()
        self.character.gift_waiting = False
        phrase = format_phrase(random.choice(GIFT_EXPIRED_PHRASES))
        crab_screen_y = self._win_y()
        self.speech.show(phrase, self._abs_x(self.character.x), crab_screen_y)
        return False

    def _hide_gift(self):
        self.gift_layer_emoji = None
        if self.gift_timer:
            GLib.source_remove(self.gift_timer)
            self.gift_timer = None

    def _collect_gift(self):
        gift = Memory.shared().collect_gift()
        if not gift:
            return
        self._hide_gift()
        self.character.gift_waiting = False
        self.speech.clear_persistent()
        phrase = format_phrase(random.choice(GIFT_COLLECT_PHRASES))
        crab_screen_y = self._win_y()
        self.speech.show(phrase, self._abs_x(self.character.x), crab_screen_y)

    # ---- Main tick ----

    def _tick(self):
        now = time.time()
        dt = (now - self.last_tick) * 1000
        self.last_tick = now
        if dt > 50:
            dt = 50

        # Startup animation
        if self.startup_phase is not None:
            self.startup_timer += dt
            if self.startup_phase == 0 and self.startup_timer > 1000:
                self.startup_phase = 1
                self.startup_timer = 0
                self.current_sprite_name = "blink"
            elif self.startup_phase == 1 and self.startup_timer > 500:
                self.startup_phase = 2
                self.startup_timer = 0
                self.current_sprite_name = "idle"
                crab_screen_y = self._win_y()
                self.speech.show(t("*зевает*"), self._abs_x(self.character.x), crab_screen_y)
            elif self.startup_phase == 2 and self.startup_timer > 1500:
                self.startup_phase = None
            self.drawing_area.queue_draw()
            return True

        # Update character
        result = self.character.update(dt)

        # Process events
        crab_screen_y = self._win_y()
        for event_type, event_data in result["events"]:
            if event_type == "particle":
                px = SPRITE_OFFSET_X + SPRITE_SIZE / 2
                py = SPRITE_OFFSET_Y + SPRITE_SIZE
                self.particles.add(event_data, px, py)
            elif event_type == "message":
                if self.character.state in ("idle", "walking"):
                    self.speech.maybe_show(
                        event_data, self._abs_x(result["x"]), crab_screen_y)
                else:
                    # Activities and reactions show immediately
                    self.speech.show(
                        event_data, self._abs_x(result["x"]), crab_screen_y)
            elif event_type == "friend_appear":
                self.friend_visible = True
            elif event_type == "friend_leave":
                self.friend_visible = False
            elif event_type == "gift":
                try:
                    self._show_gift(event_data, result["x"])
                except Exception:
                    pass
            elif event_type == "gift_star":
                try:
                    name = event_data or ""
                    Memory.shared().add_gift("star", "⭐", name=name, collected=True)
                except Exception:
                    pass

        # Update friend sprite name
        if result["friend_visible"]:
            self.friend_sprite = result.get("friend_sprite", "idle")

        # Update particles
        self.particles.update(dt)

        # Update window position (absolute screen coords)
        win_x = int(self._abs_x(result["x"]) - WINDOW_WIDTH / 2)
        win_y = self._win_y(result["y_offset"])
        self.window.move(win_x, win_y)
        part_offset = WINDOW_HEIGHT - PARTICLE_WINDOW_HEIGHT
        self.particle_window.move(win_x, win_y + part_offset)

        # Update speech bubble position
        self.speech.update_position(
            self._abs_x(result["x"]), win_y)

        # Update sprite
        sprite_name = result["sprite"]
        facing = result["facing_right"]
        if not self.sprite_cache.has(sprite_name):
            sprite_name = "idle"

        self.current_sprite_name = sprite_name
        self.current_facing = facing

        # Request redraws
        self.drawing_area.queue_draw()
        self.particle_area.queue_draw()

        return True  # keep timer alive


def main():
    signal.signal(signal.SIGINT, lambda *_: Gtk.main_quit())

    app = CrabApp()
    Gtk.main()


if __name__ == "__main__":
    main()
