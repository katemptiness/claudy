"""The drawing interface backends implement, plus a shared image cache."""

from claudy.render import art


class Canvas:
    """A backend's drawing surface for one window, for one frame.

    Coordinates are in points with the origin at the window's top-left and
    y growing downward. Colors are (r, g, b, a) floats in 0..1.
    """

    def image(self, key, x, y, alpha=1.0):
        """Draw the pixel-art image for `key` (see art.build), top-left at (x, y)."""
        raise NotImplementedError

    def rect(self, x, y, w, h, rgba):
        raise NotImplementedError

    def text(self, text, x, y, size, rgba, bold=False):
        """Draw text with its bounding box's top-left at (x, y)."""
        raise NotImplementedError

    def measure(self, text, size, bold=False):
        """(width, height) of `text` as text() would draw it."""
        raise NotImplementedError


class ImageCache:
    """Native images for art keys, built once on first use.

    `make_image(pixel_image)` is the backend's converter from an
    art.PixelImage to whatever its canvas draws.
    """

    def __init__(self, make_image):
        self._make_image = make_image
        self._images = {}

    def get(self, key):
        image = self._images.get(key)
        if image is None:
            pixels = art.build(key)
            image = self._images[key] = (self._make_image(pixels),
                                         pixels.width, pixels.height)
        return image
