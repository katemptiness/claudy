"""Speech bubble system — floating text above the crab (macOS)."""

import time
import AppKit
import Quartz


class SpeechBubble:
    """A small floating window that shows text above the crab."""

    def __init__(self):
        self.window = None
        self.text_field = None
        self.last_shown = 0
        self.min_interval = 3000  # ms between speeches (just prevents overlap)
        self.show_chance = 1.0  # frequency controlled by character timer
        self._hide_timer = None
        self._visible = False
        self._persistent = False  # blocks other messages while True

    def setup(self):
        """Create the speech bubble window (call after NSApp is running)."""
        self.window = AppKit.NSWindow.alloc().initWithContentRect_styleMask_backing_defer_(
            ((0, 0), (160, 40)),
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
        self.window.setIgnoresMouseEvents_(True)
        self.window.setAlphaValue_(0)

        # Background view with rounded corners
        content = AppKit.NSView.alloc().initWithFrame_(((0, 0), (160, 40)))
        content.setWantsLayer_(True)
        layer = content.layer()
        layer.setBackgroundColor_(
            Quartz.CGColorCreateGenericRGB(0.1, 0.1, 0.1, 0.85)
        )
        layer.setCornerRadius_(8)
        self.window.setContentView_(content)

        # Text field
        self.text_field = AppKit.NSTextField.alloc().initWithFrame_(
            ((8, 6), (144, 28))
        )
        self.text_field.setEditable_(False)
        self.text_field.setSelectable_(False)
        self.text_field.setBordered_(False)
        self.text_field.setDrawsBackground_(False)
        self.text_field.setTextColor_(AppKit.NSColor.whiteColor())
        self.text_field.setFont_(
            AppKit.NSFont.fontWithName_size_("Menlo", 11)
        )
        self.text_field.setAlignment_(AppKit.NSTextAlignmentCenter)
        content.addSubview_(self.text_field)

    def maybe_show(self, text, crab_x, crab_y):
        """Show the bubble with probability check and rate limiting."""
        if not self.window or self._persistent:
            return

        now = time.time() * 1000
        if now - self.last_shown < self.min_interval:
            return

        import random
        if random.random() > self.show_chance:
            return

        self.show(text, crab_x, crab_y)

    def show(self, text, crab_x, crab_y):
        """Show the speech bubble immediately (bypasses rate limit)."""
        if not self.window or self._persistent:
            return

        self.last_shown = time.time() * 1000
        self._visible = True

        # Size the window to fit text
        width = max(80, min(200, len(text) * 9 + 20))
        self.window.setContentSize_((width, 40))
        self.text_field.setFrame_(((8, 6), (width - 16, 28)))
        self.text_field.setStringValue_(text)

        # Position above the crab
        bubble_x = crab_x - width / 2
        bubble_y = crab_y + 90  # above the sprite
        self.window.setFrameOrigin_((bubble_x, bubble_y))

        # Fade in
        self.window.orderFront_(None)
        AppKit.NSAnimationContext.beginGrouping()
        AppKit.NSAnimationContext.currentContext().setDuration_(0.3)
        self.window.animator().setAlphaValue_(1.0)
        AppKit.NSAnimationContext.endGrouping()

        # Schedule fade out
        if self._hide_timer:
            self._hide_timer.invalidate()
        display_time = max(2.0, min(5.0, len(text) * 0.15))
        self._hide_timer = AppKit.NSTimer.scheduledTimerWithTimeInterval_target_selector_userInfo_repeats_(
            display_time, self, "hideBubble:", None, False,
        )

    def show_persistent(self, text, crab_x, crab_y, duration=300.0):
        """Show a persistent bubble that blocks other messages."""
        if not self.window:
            return
        self._persistent = True
        self.last_shown = time.time() * 1000
        self._visible = True

        width = max(80, min(200, len(text) * 9 + 20))
        self.window.setContentSize_((width, 40))
        self.text_field.setFrame_(((8, 6), (width - 16, 28)))
        self.text_field.setStringValue_(text)

        bubble_x = crab_x - width / 2
        bubble_y = crab_y + 90
        self.window.setFrameOrigin_((bubble_x, bubble_y))

        self.window.orderFront_(None)
        AppKit.NSAnimationContext.beginGrouping()
        AppKit.NSAnimationContext.currentContext().setDuration_(0.3)
        self.window.animator().setAlphaValue_(1.0)
        AppKit.NSAnimationContext.endGrouping()

        if self._hide_timer:
            self._hide_timer.invalidate()
        self._hide_timer = AppKit.NSTimer.scheduledTimerWithTimeInterval_target_selector_userInfo_repeats_(
            duration, self, "hideBubble:", None, False,
        )

    def clear_persistent(self):
        """Clear persistent mode and hide the bubble."""
        if self._persistent:
            self._persistent = False
            if self._hide_timer:
                self._hide_timer.invalidate()
                self._hide_timer = None
            self.hideBubble_(None)

    def hideBubble_(self, timer):
        """Fade out the speech bubble."""
        if not self._visible:
            return
        self._visible = False
        self._persistent = False
        AppKit.NSAnimationContext.beginGrouping()
        AppKit.NSAnimationContext.currentContext().setDuration_(0.5)
        self.window.animator().setAlphaValue_(0)
        AppKit.NSAnimationContext.endGrouping()

    def update_position(self, crab_x, crab_y):
        """Reposition the bubble if crab moves while it's visible."""
        if self._visible and self.window:
            size = self.window.frame().size
            self.window.setFrameOrigin_((
                crab_x - size.width / 2,
                crab_y + 90,
            ))
