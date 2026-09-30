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
from claudy.backends.macos.gallery_ui import GalleryWindow
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
from claudy.log import log, reported
from claudy.render.scene import Scene, star_offset_x

CLAUDE_BUNDLE_ID = "com.anthropic.claudefordesktop"
CLAUDE_WEB_URL = "https://claude.ai"

# After a display change the Dock settles on its screen a moment later, and
# the visible frame (which gives the Dock line) only follows then
SCREEN_SETTLE_S = 2

# The sprite's rect in the crab view's (unflipped, y-up) coordinates
SPRITE_RECT = ((SPRITE_X, WINDOW_HEIGHT - SPRITE_Y - SPRITE_SIZE),
               (SPRITE_SIZE, SPRITE_SIZE))


def _in_sprite(x, y):
    """Whether a point in the crab window's coordinates is on Claudy."""
    (sx, sy), (sw, sh) = SPRITE_RECT
    return sx <= x <= sx + sw and sy <= y <= sy + sh

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
        self._gifts_window.gallery = GalleryWindow.alloc().init()

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

    def gallery_changed(self):
        self._gifts_window.gallery.refresh()

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
        """Only the sprite takes clicks. The window itself only listens while
        the pointer is over the sprite (MacApp._follow_pointer); this covers
        the frame it takes to notice the pointer has left."""
        if _in_sprite(point.x, point.y):
            return objc.super(CrabView, self).hitTest_(point)
        return None

    # Every callback below runs its body under reported(): AppKit swallows
    # what a callback raises, so it would never reach error.log

    def mouseDown_(self, event):
        with reported("mouse down"):
            # Control-click is the Mac's other right-click
            if event.modifierFlags() & AppKit.NSEventModifierFlagControl:
                self.app.show_menu(event, self)
                return
            # A second press means the first one wasn't a single click after
            # all: it is becoming a double-click or a drag
            if self._click_timer is not None:
                self._click_timer.invalidate()
                self._click_timer = None
            self._pressed = True
            loc = event.locationInWindow()
            self._grab = (loc.x, loc.y)
            self._dragging = False  # becomes True on mouseDragged

    def mouseDragged_(self, event):
        with reported("drag"):
            if not self._pressed:
                return
            if not self._dragging:
                self._dragging = True
                self.app.controller.on_drag_start()
            mouse = AppKit.NSEvent.mouseLocation()
            self.app.drag_window_to(mouse.x - self._grab[0],
                                    mouse.y - self._grab[1])

    def mouseUp_(self, event):
        with reported("mouse up"):
            if not self._pressed:
                return  # the press opened the menu instead
            self._pressed = False
            if self._dragging:
                self._dragging = False
                self.app.drop_window()
                return

            # macOS counts the clicks itself, using the double-click speed
            # the user set in System Settings; a third click of a triple is
            # ignored
            clicks = event.clickCount()
            if clicks == 2:
                self.app.controller.on_double_click()
            elif clicks == 1:
                # Single click — wait as long as a double-click may take to
                # tell the two apart
                self._click_timer = AppKit.NSTimer.scheduledTimerWithTimeInterval_target_selector_userInfo_repeats_(
                    AppKit.NSEvent.doubleClickInterval(), self,
                    "singleClickFired:", None, False)

    def singleClickFired_(self, timer):
        with reported("click"):
            self._click_timer = None
            self.app.controller.on_click()

    def rightMouseDown_(self, event):
        with reported("menu"):
            self.app.show_menu(event, self)


class MenuTarget(AppKit.NSObject):
    """Receives context-menu clicks; each item's tag indexes `actions`."""

    def invoke_(self, sender):
        action = self.actions.get(sender.tag())
        if action:
            with reported("menu action"):
                action()


class MacApp:
    """Windows, drawing and the frame loop for macOS."""

    def __init__(self):
        self.settings = Settings.shared()

        self._read_screen()
        # dock_y adds the user's vertical_offset to the Dock line and is
        # refreshed every tick, so the height setting applies live (and
        # previews while dragging the slider)
        self.dock_y = self.dock_base_y + self.settings.vertical_offset
        self._screen_settles_at = None  # when to look at the screen again
        self._pointer_on_claudy = False

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

    # ---- Screen ----

    def _read_screen(self):
        """Find the primary display and the Dock line on it.

        All geometry comes from the primary display, the one with the menu
        bar, where the Dock lives unless the user moves it; Linux uses its
        primary monitor the same way. mainScreen() would be the display with
        keyboard focus, so Claudy's home would depend on which window happened
        to be focused. The controller works in x relative to that screen
        (0..screen_width); screen_x converts. Returns False while there is no
        screen at all, as can happen for a moment mid-change.
        """
        screens = AppKit.NSScreen.screens()
        if not screens:
            return False
        screen = screens[0]
        self.screen_x = screen.frame().origin.x
        self.screen_width = screen.frame().size.width
        self.dock_base_y = get_dock_top_y(screen)
        return True

    def screen_changed(self):
        """A display came, went or changed resolution: find the Dock again,
        now and once more when it has settled."""
        self._follow_screen()
        self._screen_settles_at = time.monotonic() + SCREEN_SETTLE_S

    def _follow_screen(self):
        # The windows follow on the next tick
        if self._read_screen():
            self.controller.set_screen_width(self.screen_width)

    # ---- Windows ----

    def _create_windows(self):
        # A panel, so a click on Claudy leaves the keyboard where it was. It
        # starts out ignoring the mouse; _follow_pointer lets it listen only
        # while the pointer is on Claudy
        self.window = make_overlay_window(WINDOW_WIDTH, WINDOW_HEIGHT,
                                          panel=True)
        self.window.setIgnoresMouseEvents_(True)
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
        self.window.orderFront_(None)
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
            # Behind Claudy: hung low, it is in reach of his raised claws
            # and props, and he should cover it, not it him
            self.star_window.orderWindow_relativeTo_(
                AppKit.NSWindowBelow, self.window.windowNumber())

    # ---- Pointer ----

    def _follow_pointer(self):
        """Let the crab window take the mouse only while it is on Claudy.

        A macOS window that takes the mouse takes it across its whole frame:
        there is no input shape as on Linux, and a hitTest_ that finds
        nothing stops a click at the window rather than passing it on. That
        left a dead strip around Claudy where nothing below could be clicked.
        So the window ignores the mouse unless the pointer is over the
        sprite, and hover is told here too: a window that ignores the mouse
        gets no mouseEntered or mouseExited either.
        """
        # While a button is held, things stay as they were: a drag of Claudy
        # that outruns his window keeps it, and a drag from another app
        # passes over him
        if AppKit.NSEvent.pressedMouseButtons():
            return
        mouse = AppKit.NSEvent.mouseLocation()
        origin = self.window.frame().origin
        inside = _in_sprite(mouse.x - origin.x, mouse.y - origin.y)
        if inside != self._pointer_on_claudy:
            self._pointer_on_claudy = inside
            self.window.setIgnoresMouseEvents_(not inside)
            self.controller.on_hover(inside)

    # ---- Dragging ----

    def drag_window_to(self, x, y):
        # Claudy stays on his own screen: dropped past its edge, or on
        # another display, he would be out of reach of his Dock
        x = min(max(x, self.screen_x - SPRITE_X),
                self.screen_x + self.screen_width - SPRITE_X - SPRITE_SIZE)
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
        # A click still waiting to be told apart from a double-click happens
        # now: its timer can't fire while the menu is tracking, and after
        # the menu it would cut off whatever was picked in it
        if view._click_timer is not None:
            view._click_timer.invalidate()
            view._click_timer = None
            self.controller.on_click()
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
            if (self._screen_settles_at is not None
                    and now >= self._screen_settles_at):
                self._screen_settles_at = None
                self._follow_screen()
            self.dock_y = self.dock_base_y + self.settings.vertical_offset
            view = self.controller.tick(dt)
            if not self.controller.is_dragging:
                self._move_windows(view)
            self._follow_pointer()
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
        self.app = None
        with reported("startup"):
            self.app = MacApp()
        if self.app is None:
            # With no windows at all there'd be nothing left to quit from
            AppKit.NSApp.terminate_(None)

    def tick_(self, timer):
        self.app.tick()

    def applicationDidChangeScreenParameters_(self, notification):
        with reported("screen change"):
            # It can come before launch has finished, or after it failed
            app = getattr(self, "app", None)
            if app is not None:
                app.screen_changed()


def main():
    signal.signal(signal.SIGINT, lambda *_: AppKit.NSApp.terminate_(None))
    app = AppKit.NSApplication.sharedApplication()
    delegate = AppDelegate.alloc().init()
    app.setDelegate_(delegate)
    app.run()
