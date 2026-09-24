"""Claudy — desktop companion for macOS (PyObjC/AppKit).

The Objective-C subclasses here (AppDelegate, CrabView, MenuTarget) only
receive Cocoa callbacks and forward them; the logic lives in the plain
Python MacApp and in the shared Controller.
"""

import signal
import subprocess
import time

import AppKit
import Quartz
import objc

from claudy.backends.macos.events import SystemEventObserver
from claudy.backends.macos.gifts_ui import GiftsWindow
from claudy.backends.macos.renderer import render_sprite
from claudy.backends.macos.settings_ui import SettingsWindow
from claudy.backends.macos.speech import SpeechBubble
from claudy.backends.sprite_cache import SpriteCache
from claudy.config import (
    DOCK_DEFAULT_TILE_SIZE, DOCK_TILE_GAP, DOCK_Y_ADJUST, FRIEND_OFFSET_X,
    PARTICLE_WINDOW_HEIGHT, SPRITE_OFFSET_X, SPRITE_OFFSET_Y, SPRITE_SIZE,
    TICK_INTERVAL, WINDOW_HEIGHT, WINDOW_WIDTH,
)
from claudy.content import ui_text
from claudy.core.controller import Controller, Platform
from claudy.core.settings import Settings
from claudy.log import log

# Wait this long after a click to see whether it becomes a double-click
DOUBLE_CLICK_S = 0.35
# Two clicks closer together than this count as a double-click
DOUBLE_CLICK_WINDOW_S = 0.5

SPRITE_RECT = ((SPRITE_OFFSET_X, SPRITE_OFFSET_Y), (SPRITE_SIZE, SPRITE_SIZE))

CLAUDE_CODE_SCRIPTS = {
    "iTerm2": (
        'tell application "iTerm2"\n'
        '  create window with default profile\n'
        '  tell current session of current window\n'
        '    write text "claude"\n'
        '  end tell\n'
        'end tell'
    ),
    "Warp": (
        'tell application "Warp"\n'
        '  activate\n'
        'end tell\n'
        'delay 0.5\n'
        'tell application "System Events"\n'
        '  tell process "Warp"\n'
        '    keystroke "t" using command down\n'
        '  end tell\n'
        'end tell'
    ),
    "Terminal": (
        'tell application "Terminal"\n'
        '  do script "claude"\n'
        '  activate\n'
        'end tell'
    ),
}


def get_dock_top_y():
    """Get the Y coordinate of the top of the Dock."""
    screen = AppKit.NSScreen.mainScreen()
    full = screen.frame()
    visible = screen.visibleFrame()
    dock_height = visible.origin.y - full.origin.y
    if dock_height < 10:
        dock_height = 70
    return full.origin.y + dock_height + DOCK_Y_ADJUST


def get_dock_tile_pitch():
    """Estimate the on-screen width per Dock icon (permission-free).

    Reads the Dock's 'tilesize' (the icon size) so the per-icon pitch scales
    with the user's Dock size. Falls back to the macOS default when unset.
    """
    size = DOCK_DEFAULT_TILE_SIZE
    try:
        out = subprocess.run(
            ["defaults", "read", "com.apple.dock", "tilesize"],
            capture_output=True, text=True, timeout=2)
        size = float(out.stdout.strip())
    except (ValueError, OSError, subprocess.SubprocessError):
        pass
    return size + DOCK_TILE_GAP


def open_claude():
    AppKit.NSWorkspace.sharedWorkspace().launchApplication_("Claude")


def _make_overlay_window(height):
    """A borderless, transparent window above everything, on every Space."""
    window = AppKit.NSWindow.alloc().initWithContentRect_styleMask_backing_defer_(
        ((0, 0), (WINDOW_WIDTH, height)),
        AppKit.NSWindowStyleMaskBorderless,
        AppKit.NSBackingStoreBuffered,
        False,
    )
    window.setBackgroundColor_(AppKit.NSColor.clearColor())
    window.setOpaque_(False)
    window.setHasShadow_(False)
    window.setLevel_(Quartz.CGWindowLevelForKey(Quartz.kCGMaximumWindowLevelKey))
    window.setCollectionBehavior_(
        AppKit.NSWindowCollectionBehaviorFullScreenAuxiliary
        | AppKit.NSWindowCollectionBehaviorStationary)
    return window


def _text_layer(text, size, frame):
    layer = Quartz.CATextLayer.layer()
    layer.setString_(text)
    layer.setFontSize_(size)
    layer.setAlignmentMode_(Quartz.kCAAlignmentCenter)
    layer.setContentsScale_(2.0)
    layer.setFrame_(frame)
    return layer


def _sprite_layer(frame):
    layer = Quartz.CALayer.layer()
    layer.setFrame_(frame)
    layer.setContentsGravity_(Quartz.kCAGravityResizeAspect)
    layer.setMagnificationFilter_(Quartz.kCAFilterNearest)
    return layer


class MacPlatform(Platform):
    """macOS implementations of what the controller needs."""

    def __init__(self, app):
        self._app = app
        self._settings_window = SettingsWindow.alloc().init()
        self._gifts_window = GiftsWindow.alloc().init()

    def show_speech(self, text):
        self._app.speech.show(text, *self._app.speech_anchor())

    def hide_speech(self):
        self._app.speech.hide()

    def open_claude(self):
        open_claude()

    def open_claude_code(self):
        script = CLAUDE_CODE_SCRIPTS.get(
            Settings.shared().terminal, CLAUDE_CODE_SCRIPTS["Terminal"])
        try:
            subprocess.Popen(["osascript", "-e", script])
        except OSError:
            log.exception("failed to open Claude Code")

    def open_settings(self):
        self._settings_window.show()

    def open_gifts(self):
        self._gifts_window.show()

    def show_about(self):
        alert = AppKit.NSAlert.alloc().init()
        alert.setMessageText_("Claudy")
        alert.setInformativeText_(ui_text.about_text("PyObjC"))
        alert.runModal()

    def quit(self):
        AppKit.NSApp.terminate_(None)


class CrabView(AppKit.NSView):
    """The crab window's content view: turns mouse events into input."""

    def initWithFrame_(self, frame):
        self = objc.super(CrabView, self).initWithFrame_(frame)
        if self is None:
            return None
        self.app = None  # MacApp, set right after creation
        self._click_count = 0
        self._last_click_time = 0
        self._dragging = False
        self._grab = (0, 0)  # pointer offset from the window origin
        return self

    def acceptsFirstResponder(self):
        return True

    def acceptsFirstMouse_(self, event):
        return True

    def hitTest_(self, point):
        """Only the sprite takes clicks; the rest of the window passes through."""
        (sx, sy), (sw, sh) = SPRITE_RECT
        if sx <= point.x <= sx + sw and sy <= point.y <= sy + sh:
            return objc.super(CrabView, self).hitTest_(point)
        return None

    def mouseDown_(self, event):
        now = time.time()
        if now - self._last_click_time < DOUBLE_CLICK_WINDOW_S:
            self._click_count += 1
        else:
            self._click_count = 1
        self._last_click_time = now

        loc = event.locationInWindow()
        self._grab = (loc.x, loc.y)
        self._dragging = False  # becomes True on mouseDragged

    def mouseDragged_(self, event):
        if self._click_count == 0:
            return
        if not self._dragging:
            self._dragging = True
            self.app.controller.on_drag_start()
        mouse = AppKit.NSEvent.mouseLocation()
        self.app.drag_window_to(mouse.x - self._grab[0], mouse.y - self._grab[1])

    def mouseUp_(self, event):
        if self._dragging:
            self._dragging = False
            self._click_count = 0
            self.app.drop_window()
            return

        if self._click_count == 2:
            self._click_count = 0
            self.app.controller.on_double_click()
        elif self._click_count == 1:
            # Single click — wait to tell it apart from a double-click
            AppKit.NSTimer.scheduledTimerWithTimeInterval_target_selector_userInfo_repeats_(
                DOUBLE_CLICK_S, self, "singleClickFired:", None, False)

    def singleClickFired_(self, timer):
        if self._click_count == 1:
            self.app.controller.on_click()
        self._click_count = 0

    def mouseEntered_(self, event):
        self.app.controller.on_hover(True)

    def mouseExited_(self, event):
        self.app.controller.on_hover(False)

    def rightMouseDown_(self, event):
        menu = self.app.build_menu(self.app.controller.menu())
        AppKit.NSMenu.popUpContextMenu_withEvent_forView_(menu, event, self)

    def updateTrackingAreas(self):
        for area in self.trackingAreas():
            self.removeTrackingArea_(area)
        area = AppKit.NSTrackingArea.alloc().initWithRect_options_owner_userInfo_(
            SPRITE_RECT,
            AppKit.NSTrackingMouseEnteredAndExited | AppKit.NSTrackingActiveAlways,
            self, None)
        self.addTrackingArea_(area)
        objc.super(CrabView, self).updateTrackingAreas()


class MenuTarget(AppKit.NSObject):
    """Receives context-menu clicks; each item's tag indexes `actions`."""

    def invoke_(self, sender):
        action = self.actions.get(sender.tag())
        if action:
            action()


class MacApp:
    """Windows, drawing and the frame loop for macOS."""

    def __init__(self):
        self.settings = Settings.shared()
        self.sprites = SpriteCache(render_sprite)
        self.speech = SpeechBubble()

        # dock_base_y is the Dock-top baseline; dock_y adds the user's
        # vertical_offset and is refreshed every tick so the height setting
        # applies live (and previews while dragging the slider).
        self.dock_base_y = get_dock_top_y()
        self.dock_y = self.dock_base_y + self.settings.vertical_offset
        screen_width = AppKit.NSScreen.mainScreen().frame().size.width

        self.controller = Controller(
            MacPlatform(self), screen_width, get_dock_tile_pitch())
        self.system_events = SystemEventObserver.alloc().initWithController_(
            self.controller)

        self.menu_target = MenuTarget.alloc().init()
        self.menu_target.actions = {}

        self._create_windows()
        self.last_tick = time.monotonic()
        AppKit.NSTimer.scheduledTimerWithTimeInterval_target_selector_userInfo_repeats_(
            TICK_INTERVAL, AppKit.NSApp.delegate(), "tick:", None, True)

    # ---- Windows ----

    def _create_windows(self):
        self.window = _make_overlay_window(WINDOW_HEIGHT)
        self.window.setIgnoresMouseEvents_(False)
        content = CrabView.alloc().initWithFrame_(
            ((0, 0), (WINDOW_WIDTH, WINDOW_HEIGHT)))
        content.app = self
        content.setWantsLayer_(True)
        self.window.setContentView_(content)
        self.content_layer = content.layer()

        self.sprite_layer = _sprite_layer(SPRITE_RECT)
        self.content_layer.addSublayer_(self.sprite_layer)

        # Subtle ellipse under the crab
        shadow_w, shadow_h = 50, 8
        self.shadow_layer = Quartz.CALayer.layer()
        self.shadow_layer.setFrame_((
            (SPRITE_OFFSET_X + (SPRITE_SIZE - shadow_w) / 2, SPRITE_OFFSET_Y - 4),
            (shadow_w, shadow_h)))
        self.shadow_layer.setBackgroundColor_(
            Quartz.CGColorCreateGenericRGB(0, 0, 0, 0.15))
        self.shadow_layer.setCornerRadius_(shadow_h / 2)
        self.content_layer.insertSublayer_below_(self.shadow_layer, self.sprite_layer)

        self.friend_layer = None
        self.gift_layer = None
        self.toy_layer = None
        self.current_sprite = None
        self.current_facing = None

        # Taller click-through overlay for particles floating above the crab
        self.particle_window = _make_overlay_window(PARTICLE_WINDOW_HEIGHT)
        self.particle_window.setIgnoresMouseEvents_(True)
        particle_content = AppKit.NSView.alloc().initWithFrame_(
            ((0, 0), (WINDOW_WIDTH, PARTICLE_WINDOW_HEIGHT)))
        particle_content.setWantsLayer_(True)
        self.particle_window.setContentView_(particle_content)
        self.particle_content_layer = particle_content.layer()
        self.particle_layers = []

        self._move_windows(self.controller.view)
        self._draw(self.controller.view)
        self.window.makeKeyAndOrderFront_(None)
        self.particle_window.orderFront_(None)
        AppKit.NSApp.setActivationPolicy_(AppKit.NSApplicationActivationPolicyAccessory)

    def _move_windows(self, view):
        origin = (view["x"] - WINDOW_WIDTH / 2, self.dock_y + view["y_offset"])
        self.window.setFrameOrigin_(origin)
        self.particle_window.setFrameOrigin_(origin)

    def speech_anchor(self):
        """Where speech bubbles attach: (center x, Claudy's resting line)."""
        return self.controller.view["x"], self.dock_y

    # ---- Dragging ----

    def drag_window_to(self, x, y):
        self.window.setFrameOrigin_((x, y))
        self.particle_window.setFrameOrigin_((x, y))
        self.controller.on_drag_move(x + WINDOW_WIDTH / 2)

    def drop_window(self):
        """Let go: Claudy falls from where it was dropped back to the Dock."""
        height = self.window.frame().origin.y - self.dock_y
        self.controller.on_drop(height)

    # ---- Context menu ----

    def build_menu(self, items):
        """Turn the controller's MenuItems into an NSMenu."""
        self.menu_target.actions = {}
        return self._fill_menu("Claudy", items)

    def _fill_menu(self, title, items):
        menu = AppKit.NSMenu.alloc().initWithTitle_(title)
        menu.setAutoenablesItems_(False)
        for item in items:
            if item.separator:
                menu.addItem_(AppKit.NSMenuItem.separatorItem())
                continue
            ns_item = AppKit.NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
                item.label, None, "")
            ns_item.setEnabled_(item.enabled)
            if item.submenu:
                ns_item.setSubmenu_(self._fill_menu(item.label, item.submenu))
            elif item.action:
                tag = len(self.menu_target.actions) + 1
                self.menu_target.actions[tag] = item.action
                ns_item.setTag_(tag)
                ns_item.setTarget_(self.menu_target)
                ns_item.setAction_("invoke:")
            menu.addItem_(ns_item)
        return menu

    # ---- Frame loop ----

    def tick(self):
        now = time.monotonic()
        dt = (now - self.last_tick) * 1000
        self.last_tick = now
        try:
            self.dock_y = self.dock_base_y + self.settings.vertical_offset
            view = self.controller.tick(dt)
            if not self.controller.is_dragging:
                self._move_windows(view)
            self.speech.update_position(*self.speech_anchor())
            self._draw(view)
        except Exception:
            log.exception("tick failed")

    def _draw(self, view):
        Quartz.CATransaction.begin()
        Quartz.CATransaction.setDisableActions_(True)
        self._draw_crab(view)
        self._draw_friend(view)
        self._draw_extras(view)
        self._draw_particles()
        Quartz.CATransaction.commit()

    def _draw_crab(self, view):
        sprite, facing = view["sprite"], view["facing_right"]
        if sprite != self.current_sprite or facing != self.current_facing:
            self.current_sprite, self.current_facing = sprite, facing
            self.sprite_layer.setContents_(self.sprites.get(sprite))
            self.sprite_layer.setTransform_(
                Quartz.CATransform3DIdentity if facing
                else Quartz.CATransform3DMakeScale(-1, 1, 1))
        (x, y), size = SPRITE_RECT
        self.sprite_layer.setFrame_(((x + view["shake_dx"], y), size))

    def _draw_friend(self, view):
        if view["friend_visible"]:
            if not self.friend_layer:
                (x, y), size = SPRITE_RECT
                self.friend_layer = _sprite_layer(((x + FRIEND_OFFSET_X, y), size))
                self.content_layer.insertSublayer_below_(
                    self.friend_layer, self.sprite_layer)
            self.friend_layer.setContents_(
                self.sprites.get(view["friend_sprite"], friend=True))
        elif self.friend_layer:
            self.friend_layer.removeFromSuperlayer()
            self.friend_layer = None

    def _draw_extras(self, view):
        # Gift Claudy is offering, next to it on the Dock
        emoji = self.controller.gift_emoji
        if emoji and not self.gift_layer:
            self.gift_layer = _text_layer(
                emoji, 20, ((SPRITE_OFFSET_X + SPRITE_SIZE + 5, SPRITE_OFFSET_Y),
                            (30, 30)))
            self.content_layer.addSublayer_(self.gift_layer)
        elif not emoji and self.gift_layer:
            self.gift_layer.removeFromSuperlayer()
            self.gift_layer = None

        # Toy snuggled next to sleeping Claudy
        if view["show_toy"] and not self.toy_layer:
            self.toy_layer = _text_layer(
                "🧸", 16, ((SPRITE_OFFSET_X + SPRITE_SIZE - 10, SPRITE_OFFSET_Y - 5),
                          (25, 25)))
            self.content_layer.addSublayer_(self.toy_layer)
        elif not view["show_toy"] and self.toy_layer:
            self.toy_layer.removeFromSuperlayer()
            self.toy_layer = None

    def _draw_particles(self):
        active = self.controller.particles.get_active()
        while len(self.particle_layers) > len(active):
            self.particle_layers.pop().removeFromSuperlayer()
        while len(self.particle_layers) < len(active):
            layer = _text_layer("", 12, ((0, 0), (30, 30)))
            self.particle_content_layer.addSublayer_(layer)
            self.particle_layers.append(layer)
        for layer, p in zip(self.particle_layers, active):
            layer.setString_(p.text)
            layer.setFontSize_(p.size)
            layer.setForegroundColor_(
                Quartz.CGColorCreateGenericRGB(*p.color, p.opacity))
            layer.setFrame_(((p.x - 10, p.y), (30, 30)))
            layer.setOpacity_(p.opacity)


class AppDelegate(AppKit.NSObject):

    def applicationDidFinishLaunching_(self, notification):
        self.app = MacApp()

    def tick_(self, timer):
        self.app.tick()


def main():
    signal.signal(signal.SIGINT, lambda *_: AppKit.NSApp.terminate_(None))
    app = AppKit.NSApplication.sharedApplication()
    delegate = AppDelegate.alloc().init()
    app.setDelegate_(delegate)
    app.run()
