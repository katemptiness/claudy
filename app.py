"""Claudy — desktop companion for macOS."""

import random
import time
import objc

import AppKit
import Quartz
import signal
from config import (
    SPRITE_SIZE, WINDOW_WIDTH, WINDOW_HEIGHT,
    SPRITE_OFFSET_X, SPRITE_OFFSET_Y, TICK_INTERVAL, DOCK_Y_ADJUST,
    PARTICLE_WINDOW_HEIGHT,
)
from sprite_renderer import SpriteCache
from sprites.base import ALL as BASE_SPRITES
from sprites.activities import ALL as ACTIVITY_SPRITES
from character import Character, ACTIVITIES
from particles import ParticleSystem
from animations import GravityDrop
from system_events import SystemEventHandler
from speech import SpeechBubble
from settings import Settings, SettingsWindow
from phrases import t


def get_dock_top_y():
    """Get the Y coordinate of the top of the Dock."""
    screen = AppKit.NSScreen.mainScreen()
    full = screen.frame()
    visible = screen.visibleFrame()
    dock_height = visible.origin.y - full.origin.y
    if dock_height < 10:
        dock_height = 70
    return full.origin.y + dock_height + DOCK_Y_ADJUST


# Custom NSView for mouse event handling
class CrabView(AppKit.NSView):

    def initWithFrame_(self, frame):
        self = objc.super(CrabView, self).initWithFrame_(frame)
        if self is None:
            return None

        # Click tracking
        self._click_count = 0
        self._last_click_time = 0

        # Drag tracking
        self._dragging = False
        self._drag_offset = (0, 0)

        return self

    def acceptsFirstResponder(self):
        return True

    def acceptsFirstMouse_(self, event):
        return True

    def hitTest_(self, point):
        """Only handle events on the sprite — clicks elsewhere pass through."""
        if (SPRITE_OFFSET_X <= point.x <= SPRITE_OFFSET_X + SPRITE_SIZE and
                SPRITE_OFFSET_Y <= point.y <= SPRITE_OFFSET_Y + SPRITE_SIZE):
            return objc.super(CrabView, self).hitTest_(point)
        return None

    def _hit_test(self, event):
        """Check if click is within the sprite area."""
        loc = self.convertPoint_fromView_(event.locationInWindow(), None)
        sx = SPRITE_OFFSET_X
        sy = SPRITE_OFFSET_Y
        return (sx <= loc.x <= sx + SPRITE_SIZE and
                sy <= loc.y <= sy + SPRITE_SIZE)

    def mouseDown_(self, event):
        if not self._hit_test(event):
            return

        now = time.time()
        if now - self._last_click_time < 0.5:
            self._click_count += 1
        else:
            self._click_count = 1
        self._last_click_time = now

        # Start potential drag
        win_loc = event.locationInWindow()
        win_origin = self.window().frame().origin
        self._drag_offset = (
            win_loc.x + win_origin.x,
            win_loc.y + win_origin.y,
        )
        self._drag_start_pos = (win_origin.x, win_origin.y)
        self._dragging = False  # becomes True on mouseDragged

    def mouseDragged_(self, event):
        if self._click_count == 0:
            return

        if not self._dragging:
            self._dragging = True
            delegate = AppKit.NSApp.delegate()
            delegate.character.interrupt("dragging")

        screen_loc = AppKit.NSEvent.mouseLocation()
        new_x = screen_loc.x - (self._drag_offset[0] - self._drag_start_pos[0])
        new_y = screen_loc.y - (self._drag_offset[1] - self._drag_start_pos[1])
        self.window().setFrameOrigin_((new_x, new_y))

        # Update character and particle overlay position
        delegate = AppKit.NSApp.delegate()
        delegate.particle_window.setFrameOrigin_((new_x, new_y))
        delegate.character.x = new_x + WINDOW_WIDTH / 2

    def mouseUp_(self, event):
        delegate = AppKit.NSApp.delegate()

        if self._dragging:
            # Drop with gravity
            self._dragging = False
            win_origin = self.window().frame().origin
            delegate.start_gravity_drop(win_origin.y)
            self._click_count = 0
            return

        if self._click_count == 2:
            # Double-click: open Claude.app
            AppKit.NSWorkspace.sharedWorkspace().launchApplication_("Claude")
            self._click_count = 0
        elif self._click_count == 1:
            # Single click — delay to distinguish from double
            AppKit.NSTimer.scheduledTimerWithTimeInterval_target_selector_userInfo_repeats_(
                0.35, self, "singleClickFired:", None, False,
            )

    def singleClickFired_(self, timer):
        if self._click_count == 1:
            delegate = AppKit.NSApp.delegate()
            # Happy bounce + sparkles AND hearts
            delegate.character.interrupt("happy_love")
        self._click_count = 0

    def mouseEntered_(self, event):
        delegate = AppKit.NSApp.delegate()
        if delegate.character.state not in ("dragging",) and \
           not delegate.character.state.startswith("reaction_"):
            delegate.character.interrupt("wave")

    def mouseExited_(self, event):
        delegate = AppKit.NSApp.delegate()
        if delegate.character.state == "reaction_wave":
            delegate.character._enter_idle()

    def rightMouseDown_(self, event):
        menu = AppKit.NSMenu.alloc().initWithTitle_("Claudy")

        open_item = AppKit.NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
            "Open Claude", "openClaude:", "")
        open_item.setTarget_(AppKit.NSApp.delegate())
        menu.addItem_(open_item)

        code_item = AppKit.NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
            "Open Claude Code", "openClaudeCode:", "")
        code_item.setTarget_(AppKit.NSApp.delegate())
        menu.addItem_(code_item)

        menu.addItem_(AppKit.NSMenuItem.separatorItem())

        # Activities submenu (for previewing animations)
        activities_menu = AppKit.NSMenu.alloc().initWithTitle_("Activities")
        for name in sorted(ACTIVITIES.keys()):
            item = AppKit.NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
                name.capitalize(), "playActivity:", "")
            item.setTarget_(AppKit.NSApp.delegate())
            item.setRepresentedObject_(name)
            activities_menu.addItem_(item)
        activities_item = AppKit.NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
            "Activities", None, "")
        activities_item.setSubmenu_(activities_menu)
        menu.addItem_(activities_item)

        menu.addItem_(AppKit.NSMenuItem.separatorItem())

        settings_item = AppKit.NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
            "Settings", "openSettings:", "")
        settings_item.setTarget_(AppKit.NSApp.delegate())
        menu.addItem_(settings_item)

        about_item = AppKit.NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
            "About Claudy", "showAbout:", "")
        about_item.setTarget_(AppKit.NSApp.delegate())
        menu.addItem_(about_item)

        menu.addItem_(AppKit.NSMenuItem.separatorItem())

        quit_item = AppKit.NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
            "Quit", "quitApp:", "q")
        quit_item.setTarget_(AppKit.NSApp.delegate())
        menu.addItem_(quit_item)

        AppKit.NSMenu.popUpContextMenu_withEvent_forView_(menu, event, self)

    def updateTrackingAreas(self):
        # Remove old tracking areas
        for area in self.trackingAreas():
            self.removeTrackingArea_(area)

        # Add tracking area over sprite
        opts = (AppKit.NSTrackingMouseEnteredAndExited
                | AppKit.NSTrackingActiveAlways)
        area = AppKit.NSTrackingArea.alloc().initWithRect_options_owner_userInfo_(
            ((SPRITE_OFFSET_X, SPRITE_OFFSET_Y), (SPRITE_SIZE, SPRITE_SIZE)),
            opts, self, None,
        )
        self.addTrackingArea_(area)
        objc.super(CrabView, self).updateTrackingAreas()


class AppDelegate(AppKit.NSObject):

    def applicationDidFinishLaunching_(self, notification):
        # Initialize settings
        self._settings = Settings.shared()
        self._settings_window = SettingsWindow.alloc().init()

        # Merge all sprites and build cache
        all_sprites = {}
        all_sprites.update(BASE_SPRITES)
        all_sprites.update(ACTIVITY_SPRITES)
        self.sprite_cache = SpriteCache(all_sprites)

        # Pre-render friend sprites (blue palette)
        friend_sprite_names = ["idle", "blink", "happy", "love", "wave"]
        for name in friend_sprite_names:
            if name in all_sprites:
                self.sprite_cache.add_friend(name, all_sprites[name])

        # Screen geometry
        self.dock_y = get_dock_top_y()
        screen = AppKit.NSScreen.mainScreen()
        self.screen_width = screen.frame().size.width

        # Character brain
        self.character = Character(self.screen_width)
        self.character.x = self.screen_width / 2

        # Particle system
        self.particles = ParticleSystem()

        # Gravity drop animation
        self.gravity_drop = None

        # Friend layer (for summoning activity)
        self.friend_layer = None

        # System events
        self.system_events = SystemEventHandler(self.character)

        # Speech bubble
        self.speech = SpeechBubble()
        self.speech.setup()

        # Create window
        start_x = self.character.x - WINDOW_WIDTH / 2
        rect = ((start_x, self.dock_y), (WINDOW_WIDTH, WINDOW_HEIGHT))
        self.window = AppKit.NSWindow.alloc().initWithContentRect_styleMask_backing_defer_(
            rect,
            AppKit.NSWindowStyleMaskBorderless,
            AppKit.NSBackingStoreBuffered,
            False,
        )
        self.window.setBackgroundColor_(AppKit.NSColor.clearColor())
        self.window.setOpaque_(False)
        self.window.setHasShadow_(False)
        self.window.setLevel_(
            Quartz.CGWindowLevelForKey(Quartz.kCGMaximumWindowLevelKey)
        )
        self.window.setCollectionBehavior_(
            AppKit.NSWindowCollectionBehaviorFullScreenAuxiliary
            | AppKit.NSWindowCollectionBehaviorStationary
        )
        self.window.setIgnoresMouseEvents_(False)

        # Content view — our custom CrabView
        content = CrabView.alloc().initWithFrame_(
            ((0, 0), (WINDOW_WIDTH, WINDOW_HEIGHT))
        )
        content.setWantsLayer_(True)
        self.window.setContentView_(content)
        self.content_layer = content.layer()

        # Sprite layer
        self.sprite_layer = Quartz.CALayer.layer()
        self.sprite_layer.setFrame_(
            ((SPRITE_OFFSET_X, SPRITE_OFFSET_Y), (SPRITE_SIZE, SPRITE_SIZE))
        )
        self.sprite_layer.setContents_(self.sprite_cache.get("idle"))
        self.sprite_layer.setContentsGravity_(Quartz.kCAGravityResizeAspect)
        self.sprite_layer.setMagnificationFilter_(Quartz.kCAFilterNearest)
        self.content_layer.addSublayer_(self.sprite_layer)

        # Shadow layer — subtle ellipse below the crab
        self.shadow_layer = Quartz.CALayer.layer()
        shadow_w, shadow_h = 50, 8
        shadow_x = SPRITE_OFFSET_X + (SPRITE_SIZE - shadow_w) / 2
        self.shadow_layer.setFrame_(((shadow_x, SPRITE_OFFSET_Y - 4), (shadow_w, shadow_h)))
        self.shadow_layer.setBackgroundColor_(
            Quartz.CGColorCreateGenericRGB(0, 0, 0, 0.15)
        )
        self.shadow_layer.setCornerRadius_(shadow_h / 2)
        self.content_layer.insertSublayer_below_(self.shadow_layer, self.sprite_layer)

        # Particle overlay window (taller, for floating effects above the crab)
        self.particle_window = AppKit.NSWindow.alloc().initWithContentRect_styleMask_backing_defer_(
            ((start_x, self.dock_y), (WINDOW_WIDTH, PARTICLE_WINDOW_HEIGHT)),
            AppKit.NSWindowStyleMaskBorderless,
            AppKit.NSBackingStoreBuffered,
            False,
        )
        self.particle_window.setBackgroundColor_(AppKit.NSColor.clearColor())
        self.particle_window.setOpaque_(False)
        self.particle_window.setHasShadow_(False)
        self.particle_window.setLevel_(
            Quartz.CGWindowLevelForKey(Quartz.kCGMaximumWindowLevelKey)
        )
        self.particle_window.setCollectionBehavior_(
            AppKit.NSWindowCollectionBehaviorFullScreenAuxiliary
            | AppKit.NSWindowCollectionBehaviorStationary
        )
        self.particle_window.setIgnoresMouseEvents_(True)

        particle_content = AppKit.NSView.alloc().initWithFrame_(
            ((0, 0), (WINDOW_WIDTH, PARTICLE_WINDOW_HEIGHT))
        )
        particle_content.setWantsLayer_(True)
        self.particle_window.setContentView_(particle_content)
        self.particle_content_layer = particle_content.layer()

        self.window.makeKeyAndOrderFront_(None)
        self.particle_window.orderFront_(None)
        AppKit.NSApp.setActivationPolicy_(AppKit.NSApplicationActivationPolicyAccessory)

        # Track current sprite for change detection
        self.current_sprite_name = "idle"
        self.current_facing = True

        # Particle layers pool
        self.particle_layers = []

        # Startup animation: show sleep sprite, then wake up
        self.startup_phase = 0  # 0=sleeping, 1=blink, 2=idle
        self.startup_timer = 0
        self.current_sprite_name = "sleep_a"
        self.sprite_layer.setContents_(self.sprite_cache.get("sleep_a"))

        # Start update loop
        self.last_tick = time.time()
        AppKit.NSTimer.scheduledTimerWithTimeInterval_target_selector_userInfo_repeats_(
            TICK_INTERVAL, self, "tick:", None, True,
        )

    def start_gravity_drop(self, current_y):
        """Start a gravity drop animation from current_y back to dock."""
        self.gravity_drop = GravityDrop(current_y, self.dock_y)
        self.character.interrupt("surprise")

    def quitApp_(self, sender):
        AppKit.NSApp.terminate_(None)

    def openClaude_(self, sender):
        AppKit.NSWorkspace.sharedWorkspace().launchApplication_("Claude")

    def openClaudeCode_(self, sender):
        """Open Claude Code in the configured terminal."""
        terminal = self._settings.terminal
        if terminal == "iTerm2":
            script = (
                'tell application "iTerm2"\n'
                '  create window with default profile\n'
                '  tell current session of current window\n'
                '    write text "claude"\n'
                '  end tell\n'
                'end tell'
            )
        elif terminal == "Warp":
            script = (
                'tell application "Warp"\n'
                '  activate\n'
                'end tell\n'
                'delay 0.5\n'
                'tell application "System Events"\n'
                '  tell process "Warp"\n'
                '    keystroke "t" using command down\n'
                '  end tell\n'
                'end tell'
            )
        else:  # Terminal.app
            script = (
                'tell application "Terminal"\n'
                '  do script "claude"\n'
                '  activate\n'
                'end tell'
            )
        import subprocess
        subprocess.Popen(['osascript', '-e', script])

    def playActivity_(self, sender):
        """Force-start an activity from the context menu."""
        name = sender.representedObject()
        self.character.friend_visible = False
        self._hide_friend()
        self.character._enter_idle()
        self.character._start_activity(name)

    def openSettings_(self, sender):
        """Open the settings window."""
        self._settings_window.show()

    def showAbout_(self, sender):
        alert = AppKit.NSAlert.alloc().init()
        alert.setMessageText_("Claudy")
        alert.setInformativeText_(
            "A little pixel crab companion for your desktop.\n\n"
            "Made by katemptiness & Claude Opus\n"
            "with love and PyObjC."
        )
        alert.runModal()

    def tick_(self, timer):
        now = time.time()
        dt = (now - self.last_tick) * 1000  # ms
        self.last_tick = now
        if dt > 50:
            dt = 50

        # Startup animation
        if self.startup_phase is not None:
            self.startup_timer += dt
            if self.startup_phase == 0 and self.startup_timer > 1000:
                # Wake up — show blink
                self.startup_phase = 1
                self.startup_timer = 0
                Quartz.CATransaction.begin()
                Quartz.CATransaction.setDisableActions_(True)
                self.sprite_layer.setContents_(self.sprite_cache.get("blink"))
                Quartz.CATransaction.commit()
                self.current_sprite_name = "blink"
            elif self.startup_phase == 1 and self.startup_timer > 500:
                # Open eyes
                self.startup_phase = 2
                self.startup_timer = 0
                Quartz.CATransaction.begin()
                Quartz.CATransaction.setDisableActions_(True)
                self.sprite_layer.setContents_(self.sprite_cache.get("idle"))
                Quartz.CATransaction.commit()
                self.current_sprite_name = "idle"
                self.speech.show(t("*зевает*"), self.character.x, self.dock_y)
            elif self.startup_phase == 2 and self.startup_timer > 1500:
                # Done — enter normal mode
                self.startup_phase = None
            return

        # Handle gravity drop
        if self.gravity_drop:
            new_y, done = self.gravity_drop.update(dt)
            origin_x = self.window.frame().origin.x
            self.window.setFrameOrigin_((origin_x, new_y))
            self.particle_window.setFrameOrigin_((origin_x, new_y))
            if done:
                self.gravity_drop = None
                self.character._enter_idle()
            return  # skip normal update during drop

        # Update character
        result = self.character.update(dt)

        # Process events (particles, messages)
        for event_type, event_data in result["events"]:
            if event_type == "particle":
                px = SPRITE_OFFSET_X + SPRITE_SIZE / 2
                py = SPRITE_OFFSET_Y + SPRITE_SIZE
                self.particles.add(event_data, px, py)
            elif event_type == "message":
                if self.character.state.startswith("reaction_") \
                        or self.character.state in ("summoning", "fishing"):
                    # Reactions, summoning, fishing show speech immediately
                    self.speech.show(
                        event_data, result["x"], self.dock_y
                    )
                else:
                    self.speech.maybe_show(
                        event_data, result["x"], self.dock_y
                    )
            elif event_type == "friend_appear":
                self._show_friend()
            elif event_type == "friend_leave":
                self._hide_friend()

        # Update particles
        self.particles.update(dt)

        # Update window position (skip during dragging)
        if self.character.state != "dragging":
            window_x = result["x"] - WINDOW_WIDTH / 2
            window_y = self.dock_y + result["y_offset"]
            self.window.setFrameOrigin_((window_x, window_y))
            self.particle_window.setFrameOrigin_((window_x, window_y))

        # Keep speech bubble following the crab
        self.speech.update_position(result["x"], self.dock_y + result["y_offset"])

        # Update sprite
        sprite_name = result["sprite"]
        facing = result["facing_right"]

        if not self.sprite_cache.has(sprite_name):
            sprite_name = "idle"

        needs_update = (
            sprite_name != self.current_sprite_name
            or facing != self.current_facing
        )

        if needs_update:
            self.current_sprite_name = sprite_name
            self.current_facing = facing
            Quartz.CATransaction.begin()
            Quartz.CATransaction.setDisableActions_(True)
            self.sprite_layer.setContents_(self.sprite_cache.get(sprite_name))
            if facing:
                self.sprite_layer.setTransform_(Quartz.CATransform3DIdentity)
            else:
                self.sprite_layer.setTransform_(
                    Quartz.CATransform3DMakeScale(-1, 1, 1)
                )
            Quartz.CATransaction.commit()

        # Update shake offset
        if self.character.is_shaking:
            shake_dx = (random.random() - 0.5) * 6
            self.sprite_layer.setFrame_(
                ((SPRITE_OFFSET_X + shake_dx, SPRITE_OFFSET_Y),
                 (SPRITE_SIZE, SPRITE_SIZE))
            )
        elif not needs_update:
            self.sprite_layer.setFrame_(
                ((SPRITE_OFFSET_X, SPRITE_OFFSET_Y),
                 (SPRITE_SIZE, SPRITE_SIZE))
            )

        # Update friend layer
        self._update_friend(result)

        # Render particles
        self._render_particles()

    def _show_friend(self):
        """Create and show the friend sprite layer."""
        if self.friend_layer:
            return
        self.friend_layer = Quartz.CALayer.layer()
        friend_x = SPRITE_OFFSET_X - 50
        self.friend_layer.setFrame_(
            ((friend_x, SPRITE_OFFSET_Y), (SPRITE_SIZE, SPRITE_SIZE))
        )
        self.friend_layer.setContents_(self.sprite_cache.get("friend_idle"))
        self.friend_layer.setContentsGravity_(Quartz.kCAGravityResizeAspect)
        self.friend_layer.setMagnificationFilter_(Quartz.kCAFilterNearest)
        self.content_layer.insertSublayer_below_(
            self.friend_layer, self.sprite_layer)

    def _hide_friend(self):
        """Remove the friend sprite layer."""
        if self.friend_layer:
            self.friend_layer.removeFromSuperlayer()
            self.friend_layer = None

    def _update_friend(self, result):
        """Update friend sprite if visible."""
        if not self.friend_layer:
            return
        if not result["friend_visible"]:
            return
        friend_sprite = f"friend_{result['friend_sprite']}"
        if self.sprite_cache.has(friend_sprite):
            Quartz.CATransaction.begin()
            Quartz.CATransaction.setDisableActions_(True)
            self.friend_layer.setContents_(
                self.sprite_cache.get(friend_sprite))
            Quartz.CATransaction.commit()

    def _render_particles(self):
        active = self.particles.get_active()

        Quartz.CATransaction.begin()
        Quartz.CATransaction.setDisableActions_(True)

        while len(self.particle_layers) > len(active):
            layer = self.particle_layers.pop()
            layer.removeFromSuperlayer()

        while len(self.particle_layers) < len(active):
            layer = Quartz.CATextLayer.layer()
            layer.setFontSize_(12)
            layer.setAlignmentMode_(Quartz.kCAAlignmentCenter)
            layer.setContentsScale_(2.0)
            self.particle_content_layer.addSublayer_(layer)
            self.particle_layers.append(layer)

        for i, p in enumerate(active):
            layer = self.particle_layers[i]
            layer.setString_(p.text)
            layer.setFontSize_(p.size)
            layer.setForegroundColor_(
                Quartz.CGColorCreateGenericRGB(
                    p.color[0], p.color[1], p.color[2], p.opacity
                )
            )
            layer.setFrame_(((p.x - 10, p.y), (30, 30)))
            layer.setOpacity_(p.opacity)

        Quartz.CATransaction.commit()


def main():
    # Handle Ctrl+C gracefully
    signal.signal(signal.SIGINT, lambda *_: AppKit.NSApp.terminate_(None))

    app = AppKit.NSApplication.sharedApplication()
    delegate = AppDelegate.alloc().init()
    app.setDelegate_(delegate)
    app.run()


if __name__ == "__main__":
    main()
