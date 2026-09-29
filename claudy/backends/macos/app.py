"""Claudy — desktop companion for macOS (PyObjC/AppKit).

The Objective-C subclasses here (AppDelegate, CrabView, MenuTarget) only
receive Cocoa callbacks and forward them; the logic lives in the plain
Python MacApp, the shared Controller, and the shared Scene that paints
every window.
"""

import signal
import subprocess
import time

import AppKit
import objc

from claudy.backends.macos.bubble import BubbleWindow
from claudy.backends.macos.canvas import new_image_cache
from claudy.backends.macos.events import SystemEventObserver
from claudy.backends.macos.gifts_ui import GiftsWindow
from claudy.backends.macos.settings_ui import SettingsWindow
from claudy.backends.macos.views import (
    DrawingView, add_drawing_view, make_overlay_window,
)
from claudy.config import (
    DOCK_DEFAULT_TILE_SIZE, DOCK_TILE_GAP, DOCK_Y_ADJUST, OVERLAY_HEIGHT,
    SPRITE_SIZE, SPRITE_X, SPRITE_Y, STAR_WINDOW, TICK_INTERVAL,
    WINDOW_HEIGHT, WINDOW_WIDTH,
)
from claudy.content import ui_text
from claudy.core.controller import Controller, Platform
from claudy.core.settings import Settings
from claudy.log import log
from claudy.render.scene import Scene, star_offset_x

CLAUDE_BUNDLE_ID = "com.anthropic.claudefordesktop"
CLAUDE_WEB_URL = "https://claude.ai"

# The sprite's rect in the crab view's (unflipped, y-up) coordinates
SPRITE_RECT = ((SPRITE_X, WINDOW_HEIGHT - SPRITE_Y - SPRITE_SIZE),
               (SPRITE_SIZE, SPRITE_SIZE))

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


def get_dock_top_y(screen):
    """Get the Y coordinate of the top of the Dock on `screen`."""
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
    """Open the Claude desktop app, falling back to claude.ai in the browser
    when it isn't installed (as on Linux)."""
    workspace = AppKit.NSWorkspace.sharedWorkspace()
    app_url = workspace.URLForApplicationWithBundleIdentifier_(CLAUDE_BUNDLE_ID)
    if app_url is None:
        workspace.openURL_(AppKit.NSURL.URLWithString_(CLAUDE_WEB_URL))
        return
    workspace.openApplicationAtURL_configuration_completionHandler_(
        app_url, AppKit.NSWorkspaceOpenConfiguration.configuration(), None)


class MacPlatform(Platform):
    """macOS implementations of what the controller needs."""

    def __init__(self):
        self._settings_window = SettingsWindow.alloc().init()
        self._gifts_window = GiftsWindow.alloc().init()

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
        # Claudy is rarely the active app when his menu is used, and an
        # inactive app's alert comes up without focus, maybe behind others
        AppKit.NSApp.activateIgnoringOtherApps_(True)
        alert.runModal()

    def quit(self):
        AppKit.NSApp.terminate_(None)


class CrabView(DrawingView):
    """The crab window's content view: draws Claudy, turns mouse events
    into input."""

    def initWithFrame_(self, frame):
        self = objc.super(CrabView, self).initWithFrame_(frame)
        if self is None:
            return None
        self.app = None  # MacApp, set right after creation
        self._click_timer = None  # waits to tell a click from a double-click
        self._pressed = False
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
        # Control-click is the Mac's other right-click
        if event.modifierFlags() & AppKit.NSEventModifierFlagControl:
            self.app.show_menu(event, self)
            return
        # A second press means the first one wasn't a single click after all:
        # it is becoming a double-click or a drag
        if self._click_timer is not None:
            self._click_timer.invalidate()
            self._click_timer = None
        self._pressed = True
        loc = event.locationInWindow()
        self._grab = (loc.x, loc.y)
        self._dragging = False  # becomes True on mouseDragged

    def mouseDragged_(self, event):
        if not self._pressed:
            return
        if not self._dragging:
            self._dragging = True
            self.app.controller.on_drag_start()
        mouse = AppKit.NSEvent.mouseLocation()
        self.app.drag_window_to(mouse.x - self._grab[0], mouse.y - self._grab[1])

    def mouseUp_(self, event):
        if not self._pressed:
            return  # the press opened the menu instead
        self._pressed = False
        if self._dragging:
            self._dragging = False
            self.app.drop_window()
            return

        # macOS counts the clicks itself, using the double-click speed the
        # user set in System Settings; a third click of a triple is ignored
        clicks = event.clickCount()
        if clicks == 2:
            self.app.controller.on_double_click()
        elif clicks == 1:
            # Single click — wait as long as a double-click may take to tell
            # the two apart
            self._click_timer = AppKit.NSTimer.scheduledTimerWithTimeInterval_target_selector_userInfo_repeats_(
                AppKit.NSEvent.doubleClickInterval(), self, "singleClickFired:",
                None, False)

    def singleClickFired_(self, timer):
        self._click_timer = None
        self.app.controller.on_click()

    def mouseEntered_(self, event):
        self.app.controller.on_hover(True)

    def mouseExited_(self, event):
        self.app.controller.on_hover(False)

    def rightMouseDown_(self, event):
        self.app.show_menu(event, self)

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

        # All geometry comes from the screen Claudy starts on, read once:
        # mainScreen() follows keyboard focus, so asking again later could
        # measure a different display. The controller works in x relative to
        # that screen (0..screen_width); screen_x converts.
        screen = AppKit.NSScreen.mainScreen()
        self.screen_x = screen.frame().origin.x
        self.screen_width = screen.frame().size.width
        # dock_base_y is the Dock-top baseline; dock_y adds the user's
        # vertical_offset and is refreshed every tick so the height setting
        # applies live (and previews while dragging the slider).
        self.dock_base_y = get_dock_top_y(screen)
        self.dock_y = self.dock_base_y + self.settings.vertical_offset

        self.controller = Controller(
            MacPlatform(), self.screen_width, get_dock_tile_pitch())
        self.system_events = SystemEventObserver.alloc().initWithController_(
            self.controller)

        self.scene = Scene(self.controller)
        self.images = new_image_cache()
        self.bubble = BubbleWindow(self.scene, self.images)

        self.menu_target = MenuTarget.alloc().init()
        self.menu_target.actions = {}

        self._create_windows()
        self.last_tick = time.monotonic()
        # The frame timer runs in the common run-loop modes, not only the
        # default one: an open context menu, a slider being dragged and the
        # About alert each run their own mode, and a default-mode timer would
        # freeze Claudy (and the height sliders' live preview) until they end
        self.timer = AppKit.NSTimer.timerWithTimeInterval_target_selector_userInfo_repeats_(
            TICK_INTERVAL, AppKit.NSApp.delegate(), "tick:", None, True)
        AppKit.NSRunLoop.currentRunLoop().addTimer_forMode_(
            self.timer, AppKit.NSRunLoopCommonModes)

    # ---- Windows ----

    def _create_windows(self):
        self.window = make_overlay_window(WINDOW_WIDTH, WINDOW_HEIGHT)
        self.window.setIgnoresMouseEvents_(False)
        self.crab_view = add_drawing_view(
            self.window, WINDOW_WIDTH, WINDOW_HEIGHT, self.scene.paint_crab,
            self.images, view_class=CrabView)
        self.crab_view.app = self

        # Taller click-through overlay that stays on the Dock: shadows, the
        # gift, particles floating above the crab
        self.ground_window = make_overlay_window(WINDOW_WIDTH, OVERLAY_HEIGHT)
        self.ground_window.setIgnoresMouseEvents_(True)
        self.ground_view = add_drawing_view(
            self.ground_window, WINDOW_WIDTH, OVERLAY_HEIGHT,
            self.scene.paint_ground, self.images)

        # The named star keeps a fixed spot in the sky, so it cannot live in
        # the overlay: that one rides along with Claudy as he paces the Dock
        self.star_window = make_overlay_window(STAR_WINDOW, STAR_WINDOW)
        self.star_window.setIgnoresMouseEvents_(True)
        self.star_view = add_drawing_view(
            self.star_window, STAR_WINDOW, STAR_WINDOW, self.scene.paint_star,
            self.images)

        self._move_windows(self.controller.view)
        self._place_star()
        # Ground overlay behind, the crab in front
        self.ground_window.orderFront_(None)
        self.window.makeKeyAndOrderFront_(None)
        AppKit.NSApp.setActivationPolicy_(AppKit.NSApplicationActivationPolicyAccessory)

    def _move_windows(self, view):
        """The crab window follows Claudy up and down; the overlay stays on
        the ground."""
        x = self.screen_x + view["x"] - WINDOW_WIDTH / 2
        self.window.setFrameOrigin_((x, self.dock_y + view["y_offset"]))
        self.ground_window.setFrameOrigin_((x, self.dock_y))

    def _place_star(self):
        """Hang the named star in its spot, or hide it in daylight."""
        star = self.controller.star
        if star is None:
            if self.star_window.isVisible():
                self.star_window.orderOut_(None)
            return
        self.star_window.setFrameOrigin_(
            (self.screen_x + self.screen_width / 2
             + star_offset_x(star["name"]) - STAR_WINDOW / 2,
             self.dock_y + self.settings.star_height))
        if not self.star_window.isVisible():
            self.star_window.orderFront_(None)

    # ---- Dragging ----

    def drag_window_to(self, x, y):
        self.window.setFrameOrigin_((x, y))
        self.ground_window.setFrameOrigin_((x, self.dock_y))
        # The height lets the shadow on the Dock shrink and fade under a
        # Claudy held up in the air, as it does while he falls
        self.controller.on_drag_move(x - self.screen_x + WINDOW_WIDTH / 2,
                                     height=y - self.dock_y)

    def drop_window(self):
        """Let go: Claudy falls from where it was dropped back to the Dock."""
        height = self.window.frame().origin.y - self.dock_y
        self.controller.on_drop(height)

    # ---- Context menu ----

    def show_menu(self, event, view):
        """Pop the context menu up at the click that asked for it."""
        menu = self.build_menu(self.controller.menu())
        AppKit.NSMenu.popUpContextMenu_withEvent_forView_(menu, event, view)

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
            # The bubble's tail points at the top of the crab window
            crab_top = self.window.frame().origin.y + WINDOW_HEIGHT
            self.bubble.sync(self.controller.speech,
                             self.screen_x + view["x"], crab_top)
            # Only redraw what changed: Claudy is still most of the time, and
            # repainting the transparent windows every frame costs several
            # times the CPU
            if self.scene.crab_changed():
                self.crab_view.setNeedsDisplay_(True)
            if self.scene.ground_changed():
                self.ground_view.setNeedsDisplay_(True)
            self._place_star()
            if self.scene.star_changed():
                self.star_view.setNeedsDisplay_(True)
        except Exception:
            log.exception("tick failed")


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
