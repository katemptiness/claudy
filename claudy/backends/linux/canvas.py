"""Cairo + Pango implementation of the shared Canvas (Linux)."""

import gi
gi.require_version('Pango', '1.0')
gi.require_version('PangoCairo', '1.0')
from gi.repository import Pango, PangoCairo
import cairo

from claudy.render.canvas import Canvas, ImageCache


def make_image(pixels):
    """Render an art.PixelImage to a Cairo ImageSurface."""
    surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, pixels.width, pixels.height)
    ctx = cairo.Context(surface)
    s = pixels.scale
    for y, row in enumerate(pixels.rows):
        for x, color in enumerate(row):
            if color:
                ctx.set_source_rgba(*color)
                ctx.rectangle(x * s, y * s, s, s)
                ctx.fill()
    return surface


def new_image_cache():
    return ImageCache(make_image)


def clear(cr):
    cr.set_operator(cairo.OPERATOR_SOURCE)
    cr.set_source_rgba(0, 0, 0, 0)
    cr.paint()
    cr.set_operator(cairo.OPERATOR_OVER)


def measuring_context():
    """A throwaway Cairo context, for measuring text outside of drawing."""
    return cairo.Context(cairo.ImageSurface(cairo.FORMAT_ARGB32, 1, 1))


class CairoCanvas(Canvas):

    def __init__(self, cr, images):
        self.cr = cr
        self.images = images

    def image(self, key, x, y, alpha=1.0):
        surface, _, _ = self.images.get(key)
        cr = self.cr
        cr.save()
        cr.set_source_surface(surface, x, y)
        cr.get_source().set_filter(cairo.FILTER_NEAREST)
        if alpha < 1.0:
            cr.paint_with_alpha(alpha)
        else:
            cr.paint()
        cr.restore()

    def rect(self, x, y, w, h, rgba):
        self.cr.set_source_rgba(*rgba)
        self.cr.rectangle(x, y, w, h)
        self.cr.fill()

    def _layout(self, text, size, bold):
        layout = PangoCairo.create_layout(self.cr)
        desc = Pango.FontDescription("Sans Bold" if bold else "Sans")
        desc.set_absolute_size(size * Pango.SCALE)  # px, like macOS points
        layout.set_font_description(desc)
        layout.set_text(text, -1)
        return layout

    def text(self, text, x, y, size, rgba, bold=False):
        layout = self._layout(text, size, bold)
        cr = self.cr
        cr.move_to(x, y)
        if rgba[3] < 1.0:
            # Color emoji ignore the source color; fade them as a group
            cr.push_group()
            cr.set_source_rgba(*rgba[:3], 1.0)
            PangoCairo.show_layout(cr, layout)
            cr.pop_group_to_source()
            cr.paint_with_alpha(rgba[3])
        else:
            cr.set_source_rgba(*rgba)
            PangoCairo.show_layout(cr, layout)

    def measure(self, text, size, bold=False):
        return self._layout(text, size, bold).get_pixel_size()
