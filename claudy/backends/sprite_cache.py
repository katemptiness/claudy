"""Rendered-sprite cache shared by the backends."""

from claudy.config import FRIEND_PALETTE, PALETTE
from claudy.content.sprites import SPRITES


class SpriteCache:
    """Renders each sprite once, on first use, with a backend's renderer.

    `render(grid, palette)` turns a sprite grid into a platform image.
    Unknown names fall back to the idle sprite.
    """

    def __init__(self, render):
        self._render = render
        self._cache = {}

    def get(self, name, friend=False):
        key = (name, friend)
        image = self._cache.get(key)
        if image is None:
            grid = SPRITES.get(name, SPRITES["idle"])
            palette = FRIEND_PALETTE if friend else PALETTE
            image = self._cache[key] = self._render(grid, palette)
        return image
