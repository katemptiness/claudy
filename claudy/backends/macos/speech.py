"""Speech bubble — floating text above the crab (macOS).

The bubble only displays and fades; what to say, and for how long, is
decided by the controller.
"""

import AppKit
import Quartz

FADE_IN_S = 0.3
FADE_OUT_S = 0.5
HEIGHT = 40
# The bubble's bottom edge sits this far above Claudy's resting line
ABOVE_CRAB = 90


class SpeechBubble:
    """A small click-through window that shows text above the crab."""

    def __init__(self):
        self._visible = False

        self.window = AppKit.NSWindow.alloc().initWithContentRect_styleMask_backing_defer_(
            ((0, 0), (160, HEIGHT)),
            AppKit.NSWindowStyleMaskBorderless,
            AppKit.NSBackingStoreBuffered,
            False,
        )
        self.window.setBackgroundColor_(AppKit.NSColor.clearColor())
        self.window.setOpaque_(False)
        self.window.setHasShadow_(False)
        self.window.setLevel_(
            Quartz.CGWindowLevelForKey(Quartz.kCGMaximumWindowLevelKey))
        self.window.setCollectionBehavior_(
            AppKit.NSWindowCollectionBehaviorFullScreenAuxiliary
            | AppKit.NSWindowCollectionBehaviorStationary)
        self.window.setIgnoresMouseEvents_(True)
        self.window.setAlphaValue_(0)

        # Background view with rounded corners
        content = AppKit.NSView.alloc().initWithFrame_(((0, 0), (160, HEIGHT)))
        content.setWantsLayer_(True)
        layer = content.layer()
        layer.setBackgroundColor_(
            Quartz.CGColorCreateGenericRGB(0.1, 0.1, 0.1, 0.85))
        layer.setCornerRadius_(8)
        self.window.setContentView_(content)

        self.text_field = AppKit.NSTextField.alloc().initWithFrame_(
            ((8, 6), (144, 28)))
        self.text_field.setEditable_(False)
        self.text_field.setSelectable_(False)
        self.text_field.setBordered_(False)
        self.text_field.setDrawsBackground_(False)
        self.text_field.setTextColor_(AppKit.NSColor.whiteColor())
        self.text_field.setFont_(AppKit.NSFont.fontWithName_size_("Menlo", 11))
        self.text_field.setAlignment_(AppKit.NSTextAlignmentCenter)
        content.addSubview_(self.text_field)

    def show(self, text, crab_x, crab_y):
        """Show `text` above (crab_x, crab_y), replacing any current line."""
        self._visible = True
        width = max(80, min(200, len(text) * 9 + 20))
        self.window.setContentSize_((width, HEIGHT))
        self.text_field.setFrame_(((8, 6), (width - 16, 28)))
        self.text_field.setStringValue_(text)
        self.update_position(crab_x, crab_y)
        self.window.orderFront_(None)
        self._fade_to(1.0, FADE_IN_S)

    def hide(self):
        """Fade the bubble out."""
        if self._visible:
            self._visible = False
            self._fade_to(0.0, FADE_OUT_S)

    def update_position(self, crab_x, crab_y):
        """Follow the crab while visible."""
        if self._visible:
            width = self.window.frame().size.width
            self.window.setFrameOrigin_((crab_x - width / 2, crab_y + ABOVE_CRAB))

    def _fade_to(self, alpha, seconds):
        AppKit.NSAnimationContext.beginGrouping()
        AppKit.NSAnimationContext.currentContext().setDuration_(seconds)
        self.window.animator().setAlphaValue_(alpha)
        AppKit.NSAnimationContext.endGrouping()
