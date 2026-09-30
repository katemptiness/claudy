"""The gallery: the paintings Claudy has given the user, as the gallery
window shows them (platform-independent; both backends only lay it out).

A painting given twice is one picture with two copies: they are pixel for
pixel the same, lifted off the same easel, so the gallery hangs it once and
says how many there are. Each copy keeps its own date and story.
"""

from dataclasses import dataclass

from claudy.content.gift_stories import get_story
from claudy.content.sprites.items import PAINTED
from claudy.content.ui_text import format_date, painting_title
from claudy.core.activities import PAINTING_GIFT_EMOJI

# Item name by picture: what art.item_key() takes to draw one
_ITEMS = {picture: item for item, picture in PAINTED.items()}


@dataclass(frozen=True)
class Copy:
    date: str       # as the window shows it
    story: str


@dataclass(frozen=True)
class Painting:
    picture: str    # key into PICTURES
    item: str       # the picture as an item, for art.item_key()
    title: str
    copies: tuple   # Copy, newest first

    @property
    def count(self):
        return len(self.copies)


def paintings(entries, name=""):
    """The gallery's paintings, the most recently given first.

    `entries` is Memory.get_gallery(): oldest first, one per painting
    given. A picture Claudy no longer paints is left out, as there is
    nothing to draw it with.
    """
    by_picture = {}
    for order, entry in enumerate(entries):
        picture = entry["picture"]
        if picture not in _ITEMS:
            continue
        story = get_story("painting", entry["story"], name=name,
                          emoji=PAINTING_GIFT_EMOJI[picture])
        copies = by_picture.setdefault(picture, [])
        copies.append((entry["date"], order, Copy(format_date(entry["date"]),
                                                  story)))
    newest = sorted(by_picture.items(),
                    key=lambda item: max(c[:2] for c in item[1]),
                    reverse=True)
    return [Painting(picture, _ITEMS[picture], painting_title(picture),
                     tuple(c[2] for c in sorted(copies, key=lambda c: c[:2],
                                                reverse=True)))
            for picture, copies in newest]


def copies_given(entries):
    """How many paintings the gallery holds, repeats included."""
    return sum(1 for entry in entries if entry["picture"] in _ITEMS)
