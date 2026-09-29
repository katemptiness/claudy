"""Windows and views shared by Claudy's macOS windows."""

import AppKit
import Quartz
import objc

from claudy.backends.macos.canvas import QuartzCanvas


def make_overlay_window(width, height, panel=False):
    """A borderless, transparent window above everything, on every Space.

    With `panel` it is a non-activating panel instead, for a window that
    takes clicks: clicking it doesn't make Claudy the active app, so
    whatever the user was typing in keeps the keyboard.
    """
    if panel:
        window = AppKit.NSPanel.alloc().initWithContentRect_styleMask_backing_defer_(
            ((0, 0), (width, height)),
            AppKit.NSWindowStyleMaskBorderless
            | AppKit.NSWindowStyleMaskNonactivatingPanel,
            AppKit.NSBackingStoreBuffered,
            False,
        )
        # A panel hides whenever its app isn't active, and Claudy rarely is
        window.setHidesOnDeactivate_(False)
    else:
        window = AppKit.NSWindow.alloc().initWithContentRect_styleMask_backing_defer_(
            ((0, 0), (width, height)),
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


class DrawingView(AppKit.NSView):
    """A transparent view whose content is painted by a scene function.

    Set `paint` (called with a Canvas) and `images` (an ImageCache) after
    creating it, then call setNeedsDisplay_(True) whenever it should redraw.
    """

    def initWithFrame_(self, frame):
        self = objc.super(DrawingView, self).initWithFrame_(frame)
        if self is None:
            return None
        self.paint = None
        self.images = None
        return self

    def isOpaque(self):
        return False

    def drawRect_(self, rect):
        ctx = AppKit.NSGraphicsContext.currentContext().CGContext()
        bounds = self.bounds()
        Quartz.CGContextClearRect(ctx, bounds)
        if self.paint:
            self.paint(QuartzCanvas(ctx, bounds.size.height, self.images))


def add_drawing_view(window, width, height, paint, images, view_class=DrawingView):
    view = view_class.alloc().initWithFrame_(((0, 0), (width, height)))
    view.paint = paint
    view.images = images
    view.setWantsLayer_(True)
    window.setContentView_(view)
    return view
