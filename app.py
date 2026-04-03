"""Little Claude — desktop companion for macOS."""

import random
import time
import objc

import AppKit
import Quartz
import signal
from config import (
    SPRITE_SIZE, WINDOW_WIDTH, WINDOW_HEIGHT,
    SPRITE_OFFSET_X, SPRITE_OFFSET_Y, TICK_INTERVAL, DOCK_Y_ADJUST,
)
from sprite_renderer import SpriteCache
from sprites.base import ALL as BASE_SPRITES
from sprites.activities import ALL as ACTIVITY_SPRITES
from character import Character
from particles import ParticleSystem
from animations import GravityDrop
from system_events import SystemEventHandler
from speech import SpeechBubble


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

        # Update character position to match window
        delegate = AppKit.NSApp.delegate()
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
        menu = AppKit.NSMenu.alloc().initWithTitle_("Little Claude")

        open_item = AppKit.NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
            "Open Claude", "openClaude:", "")
        open_item.setTarget_(AppKit.NSApp.delegate())
        menu.addItem_(open_item)

        menu.addItem_(AppKit.NSMenuItem.separatorItem())

        about_item = AppKit.NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
            "About Little Claude", "showAbout:", "")
        about_item.setTarget_(AppKit.NSApp.delegate())
        menu.addItem_(about_item)

        menu.addItem_(AppKit.NSMenuItem.separatorItem())

        quit_item = AppKit.NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
            "Quit", "terminate:", "q")
        quit_item.setTarget_(AppKit.NSApp)
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
        # Merge all sprites and build cache
        all_sprites = {}
        all_sprites.update(BASE_SPRITES)
        all_sprites.update(ACTIVITY_SPRITES)
        self.sprite_cache = SpriteCache(all_sprites)

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

        self.window.makeKeyAndOrderFront_(None)
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

    def openClaude_(self, sender):
        AppKit.NSWorkspace.sharedWorkspace().launchApplication_("Claude")

    def showAbout_(self, sender):
        alert = AppKit.NSAlert.alloc().init()
        alert.setMessageText_("Little Claude")
        alert.setInformativeText_(
            "A little pixel crab companion for your desktop.\n"
            "Made with love and PyObjC."
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
                self.speech.show("*зевает*", self.character.x, self.dock_y)
            elif self.startup_phase == 2 and self.startup_timer > 1500:
                # Done — enter normal mode
                self.startup_phase = None
            return

        # Handle gravity drop
        if self.gravity_drop:
            new_y, done = self.gravity_drop.update(dt)
            self.window.setFrameOrigin_((
                self.window.frame().origin.x, new_y
            ))
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
                if self.character.state.startswith("reaction_"):
                    # Reactions show speech immediately
                    self.speech.show(
                        event_data, result["x"], self.dock_y
                    )
                else:
                    self.speech.maybe_show(
                        event_data, result["x"], self.dock_y
                    )

        # Update particles
        self.particles.update(dt)

        # Update window position (skip during dragging)
        if self.character.state != "dragging":
            window_x = result["x"] - WINDOW_WIDTH / 2
            window_y = self.dock_y + result["y_offset"]
            self.window.setFrameOrigin_((window_x, window_y))

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

        # Render particles
        self._render_particles()

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
            self.content_layer.addSublayer_(layer)
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
