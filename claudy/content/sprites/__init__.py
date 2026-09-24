"""All sprite grids, keyed by name."""

from claudy.content.sprites.activities import ALL as _ACTIVITY_SPRITES
from claudy.content.sprites.base import ALL as _BASE_SPRITES

SPRITES = {**_BASE_SPRITES, **_ACTIVITY_SPRITES}
