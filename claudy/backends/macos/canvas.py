"""Quartz implementation of the shared Canvas (macOS).

Views stay unflipped (y up, as AppKit hit-testing and tracking areas
expect); the canvas converts from the scene's top-left coordinates.
"""

import AppKit
import Quartz

from claudy.render.canvas import Canvas, ImageCache


def make_image(pixels):
    """Render an art.PixelImage to a CGImage."""
    w, h, s = pixels.width, pixels.height, pixels.scale
    ctx = Quartz.CGBitmapContextCreate(
        None, w, h,
        8,      # bits per component
        w * 4,  # bytes per row
        Quartz.CGColorSpaceCreateDeviceRGB(),
        Quartz.kCGImageAlphaPremultipliedLast,
    )
    # Flip Y so the first row of pixels ends up at the top of the image
    Quartz.CGContextTranslateCTM(ctx, 0, h)
    Quartz.CGContextScaleCTM(ctx, 1, -1)
    for y, row in enumerate(pixels.rows):
        for x, color in enumerate(row):
            if color:
                Quartz.CGContextSetRGBFillColor(ctx, *color)
                Quartz.CGContextFillRect(ctx, ((x * s, y * s), (s, s)))
    return Quartz.CGBitmapContextCreateImage(ctx)


def new_image_cache():
    return ImageCache(make_image)


class QuartzCanvas(Canvas):
    """Draws into `ctx` (a CGContext) for a view `height` points tall.

    With ctx=None it can only measure text.
    """

    def __init__(self, ctx, height, images):
        self.ctx = ctx
        self.height = height
        self.images = images
        if ctx is not None:
            # Keep pixel art crisp when scaled up on Retina displays
            Quartz.CGContextSetInterpolationQuality(ctx, Quartz.kCGInterpolationNone)

    def _flip(self, y, h):
        return self.height - y - h

    def image(self, key, x, y, alpha=1.0):
        image, w, h = self.images.get(key)
        ctx = self.ctx
        Quartz.CGContextSaveGState(ctx)
        Quartz.CGContextSetAlpha(ctx, alpha)
        Quartz.CGContextDrawImage(ctx, ((x, self._flip(y, h)), (w, h)), image)
        Quartz.CGContextRestoreGState(ctx)

    def rect(self, x, y, w, h, rgba):
        Quartz.CGContextSetRGBFillColor(self.ctx, *rgba)
        Quartz.CGContextFillRect(self.ctx, ((x, self._flip(y, h)), (w, h)))

    @staticmethod
    def _attributed(text, size, rgba, bold):
        font = (AppKit.NSFont.boldSystemFontOfSize_(size) if bold
                else AppKit.NSFont.systemFontOfSize_(size))
        color = AppKit.NSColor.colorWithSRGBRed_green_blue_alpha_(*rgba)
        return AppKit.NSAttributedString.alloc().initWithString_attributes_(
            text, {AppKit.NSFontAttributeName: font,
                   AppKit.NSForegroundColorAttributeName: color})

    def text(self, text, x, y, size, rgba, bold=False):
        string = self._attributed(text, size, rgba, bold)
        box = string.size()
        # drawInRect lays text out from the rect's top in unflipped views
        string.drawInRect_(((x, self._flip(y, box.height)),
                            (box.width + 4, box.height)))

    def measure(self, text, size, bold=False):
        box = self._attributed(text, size, (0, 0, 0, 1), bold).size()
        return box.width, box.height
